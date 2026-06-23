#!/usr/bin/env python3
"""
NAVINCLUD - Motor de Consultas Avançado
Estende NavData com filtros, binning dinâmico, e persistência.
"""

import os
import re
import json
import pandas as pd
import numpy as np
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Any, Union, Literal, Callable
from enum import Enum
from collections import defaultdict

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.join(_SCRIPT_DIR, "..", "..")


class FilterOperator(Enum):
    EQ = "="
    NE = "!="
    GT = ">"
    GE = ">="
    LT = "<"
    LE = "<="
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    PATTERN = "pattern"


class BinningStrategy(Enum):
    QUANTILES = "quantiles"
    EQUAL_WIDTH = "equal_width"
    CUSTOM = "custom"
    BY_GROUP = "by_group"


class BinningScope(Enum):
    GLOBAL = "global"
    PER_GROUP = "per_group"


@dataclass
class FilterCondition:
    field: str
    operator: str
    value: Any
    display_name: Optional[str] = None
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_display(self) -> str:
        """Retorna representação legível do filtro."""
        if self.display_name:
            return self.display_name
        
        val_str = str(self.value)
        if len(val_str) > 30:
            val_str = val_str[:27] + "..."
        
        return f"{self.field} {self.operator} {val_str}"
    
    def to_dict(self) -> dict:
        """Serializa para JSON."""
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self._serialize_value(self.value),
            "display_name": self.display_name,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FilterCondition":
        """Deserializa de JSON."""
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except:
                pass
        
        return cls(
            field=data["field"],
            operator=data["operator"],
            value=cls._deserialize_value(data["value"]),
            display_name=data.get("display_name"),
            enabled=data.get("enabled", True),
            created_at=created_at
        )
    
    @staticmethod
    def _serialize_value(val: Any) -> Any:
        """Prepara valor para serialização JSON."""
        if isinstance(val, (list, tuple)):
            return list(val)
        if isinstance(val, (np.integer, np.floating)):
            return float(val)
        return val
    
    @staticmethod
    def _deserialize_value(val: Any) -> Any:
        """Restaura valor de JSON."""
        return val


@dataclass
class DerivedFieldSpec:
    name: str
    source_field: str
    strategy: str
    n_bins: int = 4
    labels: Optional[list[str]] = None
    bins: Optional[list[float]] = None
    group_by: Optional[str] = None
    scope: str = "global"
    include_right: bool = True
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "source_field": self.source_field,
            "strategy": self.strategy,
            "n_bins": self.n_bins,
            "labels": self.labels,
            "bins": self.bins,
            "group_by": self.group_by,
            "scope": self.scope,
            "include_right": self.include_right
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DerivedFieldSpec":
        return cls(**data)


@dataclass
class SavedQuery:
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    filters: list[dict]
    derived_fields: list[dict]
    directories: list[str]
    records_count: int
    has_saved_data: bool = False
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "filters": self.filters,
            "derived_fields": self.derived_fields,
            "directories": self.directories,
            "records_count": self.records_count,
            "has_saved_data": self.has_saved_data
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SavedQuery":
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            created_at=created_at,
            updated_at=updated_at,
            filters=data.get("filters", []),
            derived_fields=data.get("derived_fields", []),
            directories=data.get("directories", []),
            records_count=data.get("records_count", 0),
            has_saved_data=data.get("has_saved_data", False)
        )


class BinningEngine:
    """Motor para criação de faixas (binning) dinâmicas."""
    
    @staticmethod
    def by_quantiles(
        series: pd.Series,
        n_bins: int = 4,
        labels: Optional[list[str]] = None
    ) -> tuple[pd.Series, list[float]]:
        """Divide em N grupos com igual número de amostras (quantis)."""
        try:
            valid = series.dropna()
            if len(valid) == 0:
                return pd.Series([np.nan] * len(series), index=series.index), []
            
            q = np.linspace(0, 1, n_bins + 1)
            bins = valid.quantile(q).unique()
            bins = sorted(bins)
            
            if len(bins) < 2:
                bins = [valid.min(), valid.max()]
            
            if labels is None:
                labels = [f"Q{i+1}" for i in range(len(bins) - 1)]
            
            result = pd.cut(
                series,
                bins=bins,
                labels=labels[:len(bins)-1],
                include_lowest=True,
                right=True
            )
            return result, bins
            
        except Exception as e:
            print(f"[AVISO] Erro no binning por quantis: {e}")
            return pd.Series([np.nan] * len(series), index=series.index), []
    
    @staticmethod
    def by_equal_width(
        series: pd.Series,
        n_bins: int = 5,
        labels: Optional[list[str]] = None
    ) -> tuple[pd.Series, list[float]]:
        """Divide o range em N intervalos de largura igual."""
        try:
            valid = series.dropna()
            if len(valid) == 0:
                return pd.Series([np.nan] * len(series), index=series.index), []
            
            min_val = valid.min()
            max_val = valid.max()
            
            if min_val == max_val:
                bins = [min_val - 0.5, max_val + 0.5]
            else:
                bins = np.linspace(min_val, max_val, n_bins + 1)
            
            bins = sorted(set(bins))
            if len(bins) < 2:
                bins = [min_val - 0.5, max_val + 0.5]
            
            if labels is None:
                labels = []
                for i in range(len(bins) - 1):
                    labels.append(f"{bins[i]:.0f}-{bins[i+1]:.0f}")
            
            result = pd.cut(
                series,
                bins=bins,
                labels=labels[:len(bins)-1],
                include_lowest=True,
                right=True
            )
            return result, bins
            
        except Exception as e:
            print(f"[AVISO] Erro no binning por largura igual: {e}")
            return pd.Series([np.nan] * len(series), index=series.index), []
    
    @staticmethod
    def by_custom(
        series: pd.Series,
        bins: list[float],
        labels: Optional[list[str]] = None,
        include_right: bool = True
    ) -> tuple[pd.Series, list[float]]:
        """Usa bins definidos pelo usuário."""
        try:
            bins = sorted(set(bins))
            
            if len(bins) < 2:
                valid = series.dropna()
                if len(valid) > 0:
                    bins = [valid.min() - 0.5, valid.max() + 0.5]
                else:
                    bins = [0, 1]
            
            if labels is None:
                labels = []
                for i in range(len(bins) - 1):
                    labels.append(f"{bins[i]:.0f}-{bins[i+1]:.0f}")
            
            result = pd.cut(
                series,
                bins=bins,
                labels=labels[:len(bins)-1],
                include_lowest=True,
                right=include_right
            )
            return result, bins
            
        except Exception as e:
            print(f"[AVISO] Erro no binning custom: {e}")
            return pd.Series([np.nan] * len(series), index=series.index), []
    
    @staticmethod
    def by_group(
        df: pd.DataFrame,
        source_field: str,
        group_by_field: str,
        n_bins: int = 4,
        labels: Optional[list[str]] = None
    ) -> tuple[pd.Series, dict]:
        """Calcula bins separadamente para cada grupo.
        
        Cada grupo terá seus próprios quantis.
        """
        try:
            result = pd.Series([np.nan] * len(df), index=df.index)
            group_bins = {}
            
            groups = df[group_by_field].dropna().unique()
            
            for group in groups:
                mask = df[group_by_field] == group
                group_series = df.loc[mask, source_field]
                
                binned, bins = BinningEngine.by_quantiles(
                    group_series,
                    n_bins=n_bins,
                    labels=labels
                )
                result.loc[mask] = binned.values
                group_bins[str(group)] = list(bins)
            
            return result, group_bins
            
        except Exception as e:
            print(f"[AVISO] Erro no binning por grupo: {e}")
            return pd.Series([np.nan] * len(df), index=df.index), {}


class FilterEngine:
    """Motor de filtros com múltiplos operadores."""
    
    OPERATOR_MAP = {
        "=": lambda s, v: s == v,
        "eq": lambda s, v: s == v,
        "!=": lambda s, v: s != v,
        "ne": lambda s, v: s != v,
        ">": lambda s, v: s > v,
        "gt": lambda s, v: s > v,
        ">=": lambda s, v: s >= v,
        "ge": lambda s, v: s >= v,
        "<": lambda s, v: s < v,
        "lt": lambda s, v: s < v,
        "<=": lambda s, v: s <= v,
        "le": lambda s, v: s <= v,
    }
    
    @staticmethod
    def apply(
        df: pd.DataFrame,
        condition: FilterCondition,
        verbose: bool = False
    ) -> pd.DataFrame:
        """Aplica um filtro ao DataFrame.
        
        Retorna o DataFrame filtrado (ou original em caso de erro).
        """
        if not condition.enabled:
            return df
        
        field = condition.field
        op = condition.operator.lower()
        value = condition.value
        
        if field not in df.columns:
            if verbose:
                print(f"[AVISO] Campo '{field}' não existe. Filtro ignorado.")
            return df
        
        series = df[field]
        
        try:
            mask = FilterEngine._compute_mask(series, op, value, verbose)
            
            if mask is not None:
                return df[mask]
            else:
                return df
                
        except Exception as e:
            if verbose:
                print(f"[AVISO] Erro ao aplicar filtro '{condition.to_display()}': {e}")
            return df
    
    @staticmethod
    def _compute_mask(
        series: pd.Series,
        op: str,
        value: Any,
        verbose: bool
    ) -> Optional[pd.Series]:
        """Computa a máscara booleana para o filtro."""
        op_lower = op.lower().strip()
        
        if op_lower in FilterEngine.OPERATOR_MAP:
            return FilterEngine.OPERATOR_MAP[op_lower](series, value)
        
        elif op_lower == "in":
            if isinstance(value, (list, tuple)):
                return series.isin(value)
            else:
                return series == value
        
        elif op_lower == "not_in":
            if isinstance(value, (list, tuple)):
                return ~series.isin(value)
            else:
                return series != value
        
        elif op_lower == "between":
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                return series.between(value[0], value[1], inclusive="both")
            else:
                if verbose:
                    print(f"[AVISO] 'between' precisa de lista com 2 valores: {value}")
                return None
        
        elif op_lower == "contains":
            if pd.api.types.is_string_dtype(series) or series.dtype == object:
                pattern = str(value)
                return series.astype(str).str.contains(pattern, na=False)
            else:
                return series == value
        
        elif op_lower == "starts_with":
            if pd.api.types.is_string_dtype(series) or series.dtype == object:
                pattern = str(value)
                return series.astype(str).str.startswith(pattern, na=False)
            else:
                return None
        
        elif op_lower == "ends_with":
            if pd.api.types.is_string_dtype(series) or series.dtype == object:
                pattern = str(value)
                return series.astype(str).str.endswith(pattern, na=False)
            else:
                return None
        
        elif op_lower == "pattern" or op_lower == "regex":
            if pd.api.types.is_string_dtype(series) or series.dtype == object:
                pattern = str(value)
                try:
                    return series.astype(str).str.contains(pattern, regex=True, na=False)
                except re.error:
                    if verbose:
                        print(f"[AVISO] Regex inválido: {pattern}")
                    return None
            else:
                return None
        
        else:
            if verbose:
                print(f"[AVISO] Operador desconhecido: '{op}'")
            return None


class NavQuery:
    """Motor de consultas avançado para o NAVINCLUD.
    
    Estende NavData com:
    - Filtros com múltiplos operadores
    - Binning dinâmico (faixas)
    - Persistência de consultas
    - Cache de resultados
    
    Uso:
        >>> from nav_query import NavQuery
        >>> nq = NavQuery()
        >>> nq.load_directory("resultados/")
        >>> nq.add_filter("preTest.turma", "ends_with", "A")
        >>> nq.add_filter("testResults.correctPercent", "<", 90)
        >>> df = nq.filtered_df
    """
    
    def __init__(
        self,
        nav_data: Optional[Any] = None,
        verbose: bool = False
    ):
        from gui.nav_data import NavData
        
        self.nd = nav_data or NavData()
        self._verbose = verbose
        
        self._filters: list[FilterCondition] = []
        self._derived_fields: dict[str, DerivedFieldSpec] = {}
        self._derived_columns: set[str] = set()
        
        self._filtered_df_cache: Optional[pd.DataFrame] = None
        self._cache_dirty: bool = True
        
        self._query_dir = os.path.join(
            _PROJECT_ROOT,
            "consultas_salvas"
        )
        os.makedirs(self._query_dir, exist_ok=True)
    
    def _log(self, msg: str):
        """Loga mensagem se verbose=True."""
        if self._verbose:
            print(f"[NavQuery] {msg}")
    
    def _invalidate_cache(self):
        """Marca cache como sujo."""
        self._cache_dirty = True
        self._filtered_df_cache = None
    
    # ========== CARREGAMENTO ==========
    
    def load_directory(
        self,
        directory: str,
        progress_callback: Optional[Callable] = None
    ) -> tuple[int, int]:
        """Carrega dados de um diretório.
        
        Retorna: (quantidade_valida, quantidade_erros)
        """
        self._log(f"Carregando diretório: {directory}")
        self._invalidate_cache()
        return self.nd.load_directory(directory, progress_callback)
    
    # ========== FILTROS ==========
    
    def add_filter(
        self,
        field: str,
        operator: str,
        value: Any,
        display_name: Optional[str] = None
    ) -> "NavQuery":
        """Adiciona uma condição de filtro.
        
        Operadores disponíveis:
            - Comparação: =, !=, >, >=, <, <=
            - Contenção: in, not_in
            - Range: between (valor: [min, max])
            - String: contains, starts_with, ends_with
            - Regex: pattern
        
        Exemplos:
            >>> nq.add_filter("preTest.turma", "ends_with", "A")
            >>> nq.add_filter("testResults.correctPercent", "<", 90)
            >>> nq.add_filter("preTest.idade", "between", [15, 18])
            >>> nq.add_filter("preTest.sexo", "in", ["Feminino", "Masculino"])
        """
        cond = FilterCondition(
            field=field,
            operator=operator,
            value=value,
            display_name=display_name
        )
        self._filters.append(cond)
        self._invalidate_cache()
        self._log(f"Filtro adicionado: {cond.to_display()}")
        return self
    
    def remove_filter(self, index: int) -> "NavQuery":
        """Remove filtro por índice."""
        if 0 <= index < len(self._filters):
            removed = self._filters.pop(index)
            self._invalidate_cache()
            self._log(f"Filtro removido: {removed.to_display()}")
        return self
    
    def remove_filter_by_field(self, field: str) -> "NavQuery":
        """Remove todos os filtros de um campo."""
        new_filters = [f for f in self._filters if f.field != field]
        removed_count = len(self._filters) - len(new_filters)
        if removed_count > 0:
            self._filters = new_filters
            self._invalidate_cache()
            self._log(f"Removidos {removed_count} filtros do campo: {field}")
        return self
    
    def clear_filters(self) -> "NavQuery":
        """Remove todos os filtros."""
        count = len(self._filters)
        self._filters = []
        self._invalidate_cache()
        if count > 0:
            self._log(f"Removidos {count} filtros")
        return self
    
    def get_active_filters(self) -> list[FilterCondition]:
        """Retorna filtros ativos."""
        return [f for f in self._filters if f.enabled]
    
    def get_all_filters(self) -> list[FilterCondition]:
        """Retorna todos os filtros (incluindo desativados)."""
        return list(self._filters)
    
    def toggle_filter(self, index: int) -> "NavQuery":
        """Alterna estado ativado/desativado de um filtro."""
        if 0 <= index < len(self._filters):
            self._filters[index].enabled = not self._filters[index].enabled
            self._invalidate_cache()
            status = "ativado" if self._filters[index].enabled else "desativado"
            self._log(f"Filtro {index} {status}: {self._filters[index].to_display()}")
        return self
    
    # ========== CAMPOS DERIVADOS (BINNING) ==========
    
    def add_derived_field(
        self,
        name: str,
        source_field: str,
        strategy: Literal["quantiles", "equal_width", "custom", "by_group"],
        n_bins: int = 4,
        labels: Optional[list[str]] = None,
        bins: Optional[list[float]] = None,
        group_by: Optional[str] = None,
        scope: Literal["global", "per_group"] = "global"
    ) -> "NavQuery":
        """Cria um campo derivado com faixas (binning).
        
        Estratégias:
            - quantiles: Divide em N grupos com igual número de amostras
            - equal_width: Divide o range em N intervalos iguais
            - custom: Usa bins definidos pelo usuário
            - by_group: Calcula separadamente para cada grupo
        
        Exemplos:
            >>> # Quantis (4 grupos)
            >>> nq.add_derived_field(
            ...     "faixa_etaria",
            ...     "preTest.idade",
            ...     "quantiles",
            ...     n_bins=4
            ... )
            
            >>> # Custom
            >>> nq.add_derived_field(
            ...     "grau_deficiencia",
            ...     "testResults.correctPercent",
            ...     "custom",
            ...     bins=[0, 50, 70, 90, 100],
            ...     labels=["Severo", "Moderado", "Leve", "Normal"]
            ... )
            
            >>> # Por grupo (cada turma tem suas próprias faixas)
            >>> nq.add_derived_field(
            ...     "faixa_por_turma",
            ...     "preTest.idade",
            ...     "by_group",
            ...     group_by="preTest.turma",
            ...     scope="per_group"
            ... )
        """
        spec = DerivedFieldSpec(
            name=name,
            source_field=source_field,
            strategy=strategy,
            n_bins=n_bins,
            labels=labels,
            bins=bins,
            group_by=group_by,
            scope=scope
        )
        self._derived_fields[name] = spec
        self._derived_columns.add(name)
        self._invalidate_cache()
        self._log(f"Campo derivado adicionado: {name} ({strategy})")
        return self
    
    def remove_derived_field(self, name: str) -> "NavQuery":
        """Remove um campo derivado."""
        if name in self._derived_fields:
            del self._derived_fields[name]
            self._derived_columns.discard(name)
            self._invalidate_cache()
            self._log(f"Campo derivado removido: {name}")
        return self
    
    def list_derived_fields(self) -> dict[str, DerivedFieldSpec]:
        """Lista campos derivados configurados."""
        return dict(self._derived_fields)
    
    # ========== APLICAÇÃO E ACESSO ==========
    
    @property
    def filtered_df(self) -> pd.DataFrame:
        """DataFrame com todos os filtros e campos derivados aplicados (lazy)."""
        if self._cache_dirty or self._filtered_df_cache is None:
            self._log("Aplicando filtros e campos derivados...")
            self._apply_all()
        return self._filtered_df_cache.copy()
    
    def _apply_all(self) -> None:
        """Aplica todos os filtros e campos derivados ao DataFrame."""
        if self.nd.df.empty:
            self._filtered_df_cache = pd.DataFrame()
            self._cache_dirty = False
            return
        
        df = self.nd.df.copy()
        
        for name, spec in self._derived_fields.items():
            try:
                df = self._apply_binning(df, name, spec)
            except Exception as e:
                self._log(f"Erro ao aplicar campo derivado '{name}': {e}")
        
        for filt in self._filters:
            if not filt.enabled:
                continue
            try:
                df = FilterEngine.apply(df, filt, self._verbose)
            except Exception as e:
                self._log(f"Erro ao aplicar filtro: {e}")
        
        self._filtered_df_cache = df
        self._cache_dirty = False
        
        self._log(f"DataFrame filtrado: {len(df)} registros")
    
    def _apply_binning(
        self,
        df: pd.DataFrame,
        name: str,
        spec: DerivedFieldSpec
    ) -> pd.DataFrame:
        """Aplica uma estratégia de binning ao DataFrame."""
        source = spec.source_field
        
        if source not in df.columns:
            self._log(f"Campo origem '{source}' não existe para binning")
            return df
        
        result_series = None
        
        if spec.strategy == "quantiles":
            result_series, _ = BinningEngine.by_quantiles(
                df[source],
                n_bins=spec.n_bins,
                labels=spec.labels
            )
        
        elif spec.strategy == "equal_width":
            result_series, _ = BinningEngine.by_equal_width(
                df[source],
                n_bins=spec.n_bins,
                labels=spec.labels
            )
        
        elif spec.strategy == "custom":
            if spec.bins is None or len(spec.bins) < 2:
                self._log(f"Binning custom precisa de pelo menos 2 bins: {spec.bins}")
                return df
            
            result_series, _ = BinningEngine.by_custom(
                df[source],
                bins=spec.bins,
                labels=spec.labels,
                include_right=spec.include_right
            )
        
        elif spec.strategy == "by_group":
            if spec.group_by is None or spec.group_by not in df.columns:
                self._log(f"Binning por grupo precisa de 'group_by' válido")
                return df
            
            result_series, _ = BinningEngine.by_group(
                df,
                source_field=source,
                group_by_field=spec.group_by,
                n_bins=spec.n_bins,
                labels=spec.labels
            )
        
        else:
            self._log(f"Estratégia de binning desconhecida: {spec.strategy}")
            return df
        
        if result_series is not None:
            df[name] = result_series.astype(str)
            self._log(f"Campo derivado '{name}' aplicado com sucesso")
        
        return df
    
    # ========== AGRUPAMENTO ==========
    
    def groupby(
        self,
        group_fields: Union[str, list[str]],
        agg_specs: dict[str, list[str]]
    ) -> tuple[Optional[pd.DataFrame], Optional[str]]:
        """Agrupa e agrega o DataFrame filtrado.
        
        Args:
            group_fields: Campo ou lista de campos para agrupar
            agg_specs: Dicionário {campo: [funcoes_de_agregacao]}
                Funções: count, mean, median, std, min, max, sum,
                        first, last, var, sem, nunique
        
        Retorna: (DataFrame_resultado, mensagem_erro)
        
        Exemplo:
            >>> result, err = nq.groupby(
            ...     ["preTest.turma", "preTest.sexo"],
            ...     {
            ...         "testResults.correctPercent": ["mean", "median", "std", "min", "max"],
            ...         "testResults.avgReactionTimeMs": ["mean", "median"],
            ...         "testId": ["count"]
            ...     }
            ... )
        """
        df = self.filtered_df
        
        if df.empty:
            return None, "DataFrame vazio (nenhum dado após filtros)"
        
        if isinstance(group_fields, str):
            group_fields = [group_fields]
        
        available_groups = [f for f in group_fields if f in df.columns]
        if not available_groups:
            return None, "Nenhum dos campos de agrupamento existe nos dados"
        
        try:
            result = df.groupby(available_groups).agg(agg_specs)
            
            if isinstance(result.columns, pd.MultiIndex):
                result.columns = [
                    f"{col[0]}_{col[1]}" if col[1] else col[0]
                    for col in result.columns
                ]
            
            result = result.reset_index()
            
            self._log(f"Groupby concluído: {len(result)} grupos")
            return result, None
            
        except Exception as e:
            error_msg = f"Erro no groupby: {str(e)}"
            self._log(error_msg)
            return None, error_msg
    
    # ========== ESTATÍSTICAS ==========
    
    def describe(self, field: str) -> pd.Series:
        """Estatísticas descritivas de um campo numérico.
        
        Retorna: count, mean, std, min, 25%, 50%, 75%, max
        """
        df = self.filtered_df
        
        if field not in df.columns:
            return pd.Series(dtype=float)
        
        series = df[field]
        
        if not pd.api.types.is_numeric_dtype(series):
            try:
                series = pd.to_numeric(series, errors='coerce')
            except:
                return pd.Series(dtype=float)
        
        return series.describe()
    
    def describe_all_numeric(self) -> pd.DataFrame:
        """Estatísticas descritivas de todos os campos numéricos."""
        df = self.filtered_df
        
        if df.empty:
            return pd.DataFrame()
        
        numeric = df.select_dtypes(include=['number'])
        
        if numeric.empty:
            return pd.DataFrame()
        
        return numeric.describe().T
    
    def value_counts(
        self,
        field: str,
        normalize: bool = False,
        dropna: bool = True
    ) -> pd.Series:
        """Contagem de valores para campos categóricos.
        
        Args:
            field: Nome do campo
            normalize: Retorna proporções ao invés de contagens
            dropna: Exclui valores NaN
        """
        df = self.filtered_df
        
        if field not in df.columns:
            return pd.Series(dtype=int)
        
        return df[field].value_counts(normalize=normalize, dropna=dropna)
    
    def correlation(
        self,
        fields: Optional[list[str]] = None,
        method: str = "pearson"
    ) -> pd.DataFrame:
        """Matriz de correlação entre campos numéricos.
        
        Args:
            fields: Lista de campos específicos (None = todos numéricos)
            method: pearson, kendall, ou spearman
        """
        df = self.filtered_df
        
        if df.empty:
            return pd.DataFrame()
        
        if fields:
            numeric = df[fields].select_dtypes(include=['number'])
        else:
            numeric = df.select_dtypes(include=['number'])
        
        if numeric.empty or len(numeric.columns) < 2:
            return pd.DataFrame()
        
        try:
            return numeric.corr(method=method)
        except Exception as e:
            self._log(f"Erro no cálculo de correlação: {e}")
            return pd.DataFrame()
    
    def unique_values(self, field: str) -> list:
        """Retorna valores únicos de um campo."""
        df = self.filtered_df
        
        if field not in df.columns:
            return []
        
        return sorted(df[field].dropna().unique().tolist())
    
    # ========== PERSISTÊNCIA ==========
    
    def save_query(
        self,
        name: str,
        description: str = "",
        include_data: bool = False
    ) -> str:
        """Salva estado atual como consulta.
        
        Args:
            name: Nome da consulta
            description: Descrição opcional
            include_data: Se True, salva também os registros filtrados
                          (arquivo maior, mas não precisa recarregar)
        
        Retorna: Caminho completo do arquivo salvo
        """
        now = datetime.now()
        
        query = SavedQuery(
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
            filters=[f.to_dict() for f in self._filters],
            derived_fields=[spec.to_dict() for spec in self._derived_fields.values()],
            directories=list(self.nd.directories),
            records_count=len(self.filtered_df),
            has_saved_data=include_data
        )
        
        safe_name = re.sub(r'[^\w\s-]', '', name).strip().lower()
        safe_name = re.sub(r'[-\s]+', '_', safe_name)
        
        filename = f"{safe_name}.json"
        filepath = os.path.join(self._query_dir, filename)
        
        query_dict = query.to_dict()
        
        if include_data:
            try:
                records_json = self.filtered_df.to_json(orient='records')
                query_dict["_saved_records"] = records_json
            except Exception as e:
                self._log(f"Não foi possível salvar os dados: {e}")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(query_dict, f, indent=2, ensure_ascii=False)
            
            self._log(f"Consulta salva em: {filepath}")
            return filepath
            
        except Exception as e:
            error_msg = f"Erro ao salvar consulta: {e}"
            self._log(error_msg)
            raise IOError(error_msg)
    
    def load_query(self, name: str) -> "NavQuery":
        """Carrega uma consulta salva.
        
        Args:
            name: Nome da consulta (sem .json) ou caminho completo
        
        Retorna: Self (para encadeamento)
        """
        if os.path.isfile(name):
            filepath = name
        else:
            safe_name = re.sub(r'[^\w\s-]', '', name).strip().lower()
            safe_name = re.sub(r'[-\s]+', '_', safe_name)
            filename = f"{safe_name}.json"
            filepath = os.path.join(self._query_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Consulta não encontrada: {name}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            query = SavedQuery.from_dict({k: v for k, v in data.items() if k != "_saved_records"})
            
            self._filters = [FilterCondition.from_dict(f) for f in query.filters]
            self._derived_fields = {
                spec["name"]: DerivedFieldSpec.from_dict(spec)
                for spec in query.derived_fields
            }
            self._derived_columns = set(self._derived_fields.keys())
            self._invalidate_cache()
            
            if "_saved_records" in data and data["_saved_records"]:
                try:
                    saved_df = pd.read_json(data["_saved_records"], orient='records')
                    self._filtered_df_cache = saved_df
                    self._cache_dirty = False
                    self._log(f"Dados carregados da consulta: {len(saved_df)} registros")
                except Exception as e:
                    self._log(f"Não foi possível carregar os dados salvos: {e}")
            
            self._log(f"Consulta carregada: {query.name}")
            return self
            
        except Exception as e:
            error_msg = f"Erro ao carregar consulta: {e}"
            self._log(error_msg)
            raise IOError(error_msg)
    
    def list_saved_queries(self) -> list[dict]:
        """Lista todas as consultas salvas.
        
        Retorna: Lista de dicionários com nome, descrição, data, contagem
        """
        result = []
        
        if not os.path.exists(self._query_dir):
            return result
        
        for filename in os.listdir(self._query_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self._query_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                result.append({
                    "name": data.get("name", filename),
                    "description": data.get("description", ""),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "records_count": data.get("records_count", 0),
                    "has_saved_data": data.get("has_saved_data", False),
                    "filters_count": len(data.get("filters", [])),
                    "derived_count": len(data.get("derived_fields", [])),
                    "filename": filename
                })
            except:
                continue
        
        return sorted(result, key=lambda x: x.get("updated_at", ""), reverse=True)
    
    def delete_query(self, name: str) -> bool:
        """Remove uma consulta salva.
        
        Retorna: True se removido com sucesso
        """
        if os.path.isfile(name):
            filepath = name
        else:
            safe_name = re.sub(r'[^\w\s-]', '', name).strip().lower()
            safe_name = re.sub(r'[-\s]+', '_', safe_name)
            filename = f"{safe_name}.json"
            filepath = os.path.join(self._query_dir, filename)
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                self._log(f"Consulta removida: {name}")
                return True
            except:
                return False
        
        return False
    
    # ========== CONVENIÊNCIA (WRAPPERS DO NavData) ==========
    
    @property
    def records(self) -> list[dict]:
        return self.nd.records
    
    @property
    def df(self) -> pd.DataFrame:
        return self.nd.df
    
    @property
    def categorized(self) -> dict:
        return self.nd.categorized
    
    @property
    def fields_info(self) -> dict:
        return self.nd.fields_info
    
    @property
    def directories(self) -> list[str]:
        return self.nd.directories
    
    @property
    def metadata(self) -> dict:
        return self.nd.metadata
    
    def get_summary_stats(self) -> dict:
        return self.nd.get_summary_stats()
    
    def get_fields_by_category(self) -> dict:
        return self.nd.get_fields_by_category()
    
    def get_active_field_keys(self) -> list[str]:
        return self.nd.get_active_field_keys()
    
    # ========== MÉTODOS DE CONVENIÊNCIA ADICIONAIS ==========
    
    def sample(self, n: int = 5) -> pd.DataFrame:
        """Retorna uma amostra aleatória dos dados filtrados."""
        df = self.filtered_df
        if df.empty:
            return df
        return df.sample(min(n, len(df)))
    
    def head(self, n: int = 5) -> pd.DataFrame:
        """Retorna as primeiras linhas."""
        return self.filtered_df.head(n)
    
    def tail(self, n: int = 5) -> pd.DataFrame:
        """Retorna as últimas linhas."""
        return self.filtered_df.tail(n)
    
    @property
    def shape(self) -> tuple[int, int]:
        """Retorna (linhas, colunas) do DataFrame filtrado."""
        return self.filtered_df.shape
    
    @property
    def columns(self) -> list[str]:
        """Retorna todas as colunas disponíveis."""
        return list(self.filtered_df.columns)
    
    def __len__(self) -> int:
        """Retorna quantidade de registros filtrados."""
        return len(self.filtered_df)
    
    def __repr__(self) -> str:
        return f"<NavQuery filters={len(self.get_active_filters())} records={len(self)}>"
