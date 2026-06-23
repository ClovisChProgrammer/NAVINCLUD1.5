#!/usr/bin/env python3
"""
NAVINCLUD - Visualização Avançada
Novos tipos de gráfico: Linha, Linha+Barra, Boxplot, Scatter, Heatmap, Comparativo

Usa matplotlib (padrão) ou seaborn (se disponível) para gráficos mais bonitos.
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, Union, Literal, Any
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

try:
    from scipy.stats import linregress
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class NavCharts:
    """Visualização avançada para o NAVINCLUD.
    
    Tipos de gráfico disponíveis:
        - barras: Gráfico de barras (padrão)
        - linha: Gráfico de linha para tendências
        - linha_barra: Gráfico combinado com 2 eixos Y
        - boxplot: Distribuição completa (mediana, quartis, outliers)
        - scatter: Correlação entre duas variáveis
        - heatmap: Matriz de correlação
        - comparativo: Grid de subplots lado-a-lado
    
    Uso:
        >>> from nav_charts import NavCharts
        >>> from nav_query import NavQuery
        >>> 
        >>> nq = NavQuery()
        >>> nq.load_directory("resultados/")
        >>> 
        >>> charts = NavCharts(nq)
        >>> 
        >>> # Boxplot: distribuição de % acertos por turma
        >>> fig = charts.boxplot(
        ...     x="preTest.turma",
        ...     y="testResults.correctPercent",
        ...     hue="preTest.sexo",
        ...     title="Distribuição de % Acertos por Turma"
        ... )
        >>> 
        >>> # Salvar gráfico
        >>> charts.save_current("boxplot_turma.png", dpi=150)
        >>> 
        >>> # Scatter: correlação entre tempo de reação e acertos
        >>> fig = charts.scatter(
        ...     x="testResults.avgReactionTimeMs",
        ...     y="testResults.correctPercent",
        ...     hue="preTest.sexo",
        ...     title="Tempo de Reação vs % Acertos",
        ...     add_trendline=True
        ... )
    """
    
    def __init__(
        self,
        nav_query: Optional[Any] = None,
        style: str = "default",
        figsize: tuple[float, float] = (10, 6)
    ):
        self.nq = nav_query
        self.figsize = figsize
        self.current_fig: Optional[Figure] = None
        self._chart_figures: list[Figure] = []
        
        plt.style.use(style)
        
        if HAS_SEABORN:
            sns.set_context("notebook")
            sns.set_palette("Set2")
    
    def _get_df(self, df: Optional[pd.DataFrame]) -> pd.DataFrame:
        """Obtém DataFrame: do parâmetro ou do NavQuery."""
        if df is not None:
            return df
        if self.nq is not None and hasattr(self.nq, 'filtered_df'):
            return self.nq.filtered_df
        raise ValueError("Nenhum DataFrame fornecido e NavQuery não configurado")
    
    def _validate_columns(self, df: pd.DataFrame, *cols: str) -> tuple[bool, str]:
        """Valida se colunas existem no DataFrame."""
        for col in cols:
            if col not in df.columns:
                return False, f"Coluna '{col}' não existe no DataFrame"
        return True, ""
    
    # ========== GRÁFICOS NOVOS ==========
    
    def linha(
        self,
        x: str,
        y: Union[str, list[str]],
        hue: Optional[str] = None,
        marker: bool = True,
        title: Optional[str] = None,
        df: Optional[pd.DataFrame] = None
    ) -> Figure:
        """Gráfico de linha para tendências.
        
        Ideal para:
            - Visualizar tendências ao longo de grupos categóricos
            - Comparar múltiplas métricas no mesmo eixo Y
        
        Args:
            x: Campo para eixo X (geralmente categórico)
            y: Campo ou lista de campos para eixo Y
            hue: Campo para cores/categorias (opcional)
            marker: Mostrar marcadores nos pontos
            title: Título do gráfico
            df: DataFrame alternativo (usa NavQuery se None)
        
        Retorna: Figure do matplotlib
        """
        data = self._get_df(df)
        
        valid, err = self._validate_columns(data, x)
        if not valid:
            fig, ax = plt.subplots(figsize=self.figsize)
            ax.text(0.5, 0.5, err, ha='center', va='center', fontsize=12)
            ax.set_title("Erro")
            self.current_fig = fig
            return fig
        
        y_fields = [y] if isinstance(y, str) else y
        
        fig, ax = plt.subplots(figsize=self.figsize)
        
        for y_field in y_fields:
            if y_field not in data.columns:
                continue
            
            if hue and hue in data.columns:
                for cat in sorted(data[hue].dropna().unique()):
                    subset = data[data[hue] == cat]
                    agg = subset.groupby(x)[y_field].mean().reset_index()
                    ax.plot(
                        agg[x].astype(str),
                        agg[y_field],
                        marker='o' if marker else '',
                        linewidth=2,
                        label=f"{cat}: {y_field}"
                    )
            else:
                agg = data.groupby(x)[y_field].mean().reset_index()
                ax.plot(
                    agg[x].astype(str),
                    agg[y_field],
                    marker='o' if marker else '',
                    linewidth=2,
                    label=y_field
                )
        
        ax.set_xlabel(x)
        ax.set_ylabel("Valor")
        if title:
            ax.set_title(title, fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        fig.tight_layout()
        
        self.current_fig = fig
        self._chart_figures.append(fig)
        return fig
    
    def linha_barra(
        self,
        x: str,
        y_linha: str,
        y_barra: str,
        hue: Optional[str] = None,
        title: Optional[str] = None,
        agg_linha: str = "mean",
        agg_barra: str = "count",
        df: Optional[pd.DataFrame] = None
    ) -> Figure:
        """Gráfico combinado: Linha + Barras com 2 eixos Y.
        
        Ideal para:
            - Comparar métricas de escala diferente
            - Ex: % de acertos (linha) vs contagem (barras)
        
        Args:
            x: Campo para eixo X
            y_linha: Campo para a linha (eixo Y direito)
            y_barra: Campo para as barras (eixo Y esquerdo)
            hue: Campo para cores (opcional)
            title: Título do gráfico
            agg_linha: Função de agregação para a linha (mean, median, etc.)
            agg_barra: Função de agregação para barras (count, mean, etc.)
            df: DataFrame alternativo
        
        Retorna: Figure do matplotlib
        """
        data = self._get_df(df)
        
        valid, err = self._validate_columns(data, x)
        if not valid:
            fig, ax = plt.subplots(figsize=self.figsize)
            ax.text(0.5, 0.5, err, ha='center', va='center', fontsize=12)
            ax.set_title("Erro")
            self.current_fig = fig
            return fig
        
        fig, ax1 = plt.subplots(figsize=self.figsize)
        ax2 = ax1.twinx()
        
        grouped = data.groupby(x)
        
        if agg_barra == "count":
            bar_data = grouped.size()
        elif y_barra in data.columns:
            bar_data = grouped[y_barra].agg(agg_barra)
        else:
            bar_data = grouped.size()
        
        x_pos = np.arange(len(bar_data))
        x_labels = bar_data.index.astype(str)
        
        bars = ax1.bar(
            x_pos,
            bar_data.values,
            alpha=0.6,
            color='#4A90D9',
            label=f"{y_barra} ({agg_barra})"
        )
        ax1.set_xlabel(x)
        ax1.set_ylabel(y_barra, color='#4A90D9')
        ax1.tick_params(axis='y', labelcolor='#4A90D9')
        
        if y_linha in data.columns:
            line_data = grouped[y_linha].agg(agg_linha)
            
            ax2.plot(
                x_pos,
                line_data.values,
                color='#E74C3C',
                marker='o',
                linewidth=2,
                label=f"{y_linha} ({agg_linha})"
            )
            ax2.set_ylabel(y_linha, color='#E74C3C')
            ax2.tick_params(axis='y', labelcolor='#E74C3C')
        
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(x_labels, rotation=45, ha='right')
        
        if title:
            ax1.set_title(title, fontsize=14)
        
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        fig.tight_layout()
        
        self.current_fig = fig
        self._chart_figures.append(fig)
        return fig
    
    def boxplot(
        self,
        x: str,
        y: str,
        hue: Optional[str] = None,
        showfliers: bool = True,
        title: Optional[str] = None,
        df: Optional[pd.DataFrame] = None
    ) -> Figure:
        """Boxplot para visualizar distribuição completa.
        
        Mostra:
            - Mediana (linha central)
            - Quartis (caixa: Q1-Q3)
            - Whiskers (linhas: Q1-1.5*IQR até Q3+1.5*IQR)
            - Outliers (pontos fora dos whiskers)
        
        Ideal para:
            - Comparar distribuições entre grupos
            - Identificar outliers
            - Ver simetria dos dados
        
        Args:
            x: Campo categórico para eixo X
            y: Campo numérico para eixo Y
            hue: Campo para cores (opcional)
            showfliers: Mostrar outliers
            title: Título do gráfico
            df: DataFrame alternativo
        
        Retorna: Figure do matplotlib
        """
        data = self._get_df(df)
        
        valid, err = self._validate_columns(data, x, y)
        if not valid:
            fig, ax = plt.subplots(figsize=self.figsize)
            ax.text(0.5, 0.5, err, ha='center', va='center', fontsize=12)
            ax.set_title("Erro")
            self.current_fig = fig
            return fig
        
        fig, ax = plt.subplots(figsize=self.figsize)
        
        if HAS_SEABORN:
            sns.boxplot(
                data=data,
                x=x,
                y=y,
                hue=hue,
                showfliers=showfliers,
                ax=ax,
                palette="Set2"
            )
        else:
            categories = sorted(data[x].dropna().unique())
            box_data = []
            labels = []
            
            for cat in categories:
                subset = data[data[x] == cat][y].dropna()
                if len(subset) > 0:
                    box_data.append(subset.values)
                    labels.append(str(cat))
            
            bp = ax.boxplot(
                box_data,
                labels=labels,
                showfliers=showfliers,
                patch_artist=True
            )
            
            colors = plt.cm.Set2(np.linspace(0, 1, len(box_data)))
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
        
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        if title:
            ax.set_title(title, fontsize=14)
        plt.xticks(rotation=45, ha='right')
        fig.tight_layout()
        
        self.current_fig = fig
        self._chart_figures.append(fig)
        return fig
    
    def scatter(
        self,
        x: str,
        y: str,
        hue: Optional[str] = None,
        size: Optional[str] = None,
        title: Optional[str] = None,
        alpha: float = 0.7,
        add_trendline: bool = True,
        df: Optional[pd.DataFrame] = None
    ) -> Figure:
        """Scatter plot para visualizar correlação entre duas variáveis.
        
        Ideal para:
            - Ver relação entre duas variáveis numéricas
            - Identificar padrões e clusters
            - Verificar correlação (com linha de tendência)
        
        Args:
            x: Campo numérico para eixo X
            y: Campo numérico para eixo Y
            hue: Campo para cores (opcional)
            size: Campo para tamanho dos pontos (opcional)
            title: Título do gráfico
            alpha: Transparência dos pontos
            add_trendline: Adicionar linha de tendência (se scipy disponível)
            df: DataFrame alternativo
        
        Retorna: Figure do matplotlib
        """
        data = self._get_df(df)
        
        valid, err = self._validate_columns(data, x, y)
        if not valid:
            fig, ax = plt.subplots(figsize=self.figsize)
            ax.text(0.5, 0.5, err, ha='center', va='center', fontsize=12)
            ax.set_title("Erro")
            self.current_fig = fig
            return fig
        
        fig, ax = plt.subplots(figsize=self.figsize)
        
        valid_data = data[[x, y]].dropna()
        
        if hue and hue in data.columns:
            for cat in sorted(data[hue].dropna().unique()):
                subset = data[data[hue] == cat]
                ax.scatter(
                    subset[x],
                    subset[y],
                    alpha=alpha,
                    label=str(cat),
                    s=60
                )
            ax.legend()
        else:
            scatter = ax.scatter(
                valid_data[x],
                valid_data[y],
                alpha=alpha,
                c=valid_data[y] if len(valid_data) > 0 else None,
                cmap='viridis' if len(valid_data) > 0 else None,
                s=60
            )
            if len(valid_data) > 0:
                plt.colorbar(scatter, ax=ax, label=y)
        
        if add_trendline and HAS_SCIPY and len(valid_data) > 2:
            try:
                slope, intercept, r, p, se = linregress(valid_data[x], valid_data[y])
                x_range = np.linspace(valid_data[x].min(), valid_data[x].max(), 100)
                ax.plot(
                    x_range,
                    intercept + slope * x_range,
                    'r--',
                    alpha=0.5,
                    label=f'Tendência (r={r:.2f}, p={p:.3f})'
                )
                ax.legend()
            except Exception:
                pass
        
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        if title:
            ax.set_title(title, fontsize=14)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        
        self.current_fig = fig
        self._chart_figures.append(fig)
        return fig
    
    def heatmap(
        self,
        fields: Optional[list[str]] = None,
        correlation: bool = True,
        cmap: str = "coolwarm",
        title: Optional[str] = None,
        annotate: bool = True,
        df: Optional[pd.DataFrame] = None
    ) -> Figure:
        """Heatmap de correlação ou de valores.
        
        Ideal para:
            - Ver correlação entre múltiplas variáveis numéricas
            - Identificar padrões de covariância
            - Visualizar matrizes de dados
        
        Args:
            fields: Lista de campos específicos (None = todos numéricos)
            correlation: Se True, calcula matriz de correlação. Se False, usa valores diretamente.
            cmap: Paleta de cores (coolwarm, viridis, RdYlGn, etc.)
            title: Título do gráfico
            annotate: Mostrar valores nas células
            df: DataFrame alternativo
        
        Retorna: Figure do matplotlib
        """
        data = self._get_df(df)
        
        if fields:
            data = data[fields]
        
        numeric = data.select_dtypes(include=['number'])
        
        if numeric.empty or len(numeric.columns) < 2:
            fig, ax = plt.subplots(figsize=self.figsize)
            ax.text(
                0.5, 0.5,
                "Necessário pelo menos 2 campos numéricos para heatmap",
                ha='center', va='center', fontsize=12
            )
            ax.set_title("Erro")
            self.current_fig = fig
            return fig
        
        fig, ax = plt.subplots(figsize=(max(8, len(numeric.columns)), 
                                      max(6, len(numeric.columns) * 0.6)))
        
        if correlation:
            matrix = numeric.corr()
            display_title = title or "Matriz de Correlação"
        else:
            matrix = numeric
            display_title = title or "Heatmap"
        
        if HAS_SEABORN:
            sns.heatmap(
                matrix,
                annot=annotate,
                cmap=cmap,
                center=0 if correlation else None,
                square=True,
                fmt='.2f' if correlation else '.0f',
                ax=ax
            )
        else:
            im = ax.imshow(matrix.values, cmap=cmap)
            ax.set_xticks(range(len(matrix.columns)))
            ax.set_yticks(range(len(matrix.index)))
            ax.set_xticklabels(matrix.columns, rotation=45, ha='right')
            ax.set_yticklabels(matrix.index)
            plt.colorbar(im, ax=ax)
        
        ax.set_title(display_title, fontsize=14)
        fig.tight_layout()
        
        self.current_fig = fig
        self._chart_figures.append(fig)
        return fig
    
    def comparativo(
        self,
        group_field: str,
        metric: str,
        chart_type: Literal["barras", "boxplot", "histograma"] = "barras",
        cols: int = 2,
        title: Optional[str] = None,
        df: Optional[pd.DataFrame] = None
    ) -> Figure:
        """Grid de comparação lado-a-lado por categoria.
        
        Ideal para:
            - Comparar distribuição de uma métrica entre subgrupos
            - Ex: Comparar % de acertos de CADA turma individualmente
        
        Args:
            group_field: Campo categórico para dividir os subplots
            metric: Campo numérico para visualizar
            chart_type: Tipo de gráfico em cada subplot: barras, boxplot, histograma
            cols: Número de colunas no grid
            title: Título principal
            df: DataFrame alternativo
        
        Retorna: Figure do matplotlib
        """
        data = self._get_df(df)
        
        valid, err = self._validate_columns(data, group_field)
        if not valid:
            fig, ax = plt.subplots(figsize=self.figsize)
            ax.text(0.5, 0.5, err, ha='center', va='center', fontsize=12)
            ax.set_title("Erro")
            self.current_fig = fig
            return fig
        
        categories = sorted(data[group_field].dropna().unique())
        n_cats = len(categories)
        
        if n_cats == 0:
            fig, ax = plt.subplots(figsize=self.figsize)
            ax.text(0.5, 0.5, "Nenhuma categoria encontrada", ha='center', va='center')
            self.current_fig = fig
            return fig
        
        rows = (n_cats + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
        if n_cats == 1:
            axes = np.array([axes])
        axes_flat = axes.flatten()
        
        display_title = title or f"Comparativo: {metric} por {group_field}"
        fig.suptitle(display_title, fontsize=14, y=1.02)
        
        for i, cat in enumerate(categories):
            if i >= len(axes_flat):
                break
            
            ax = axes_flat[i]
            subset = data[data[group_field] == cat]
            
            if metric in subset.columns:
                metric_data = subset[metric].dropna()
                
                if chart_type == "barras":
                    agg = subset.groupby(group_field)[metric].mean()
                    ax.bar([str(cat)], agg.values, color='#4A90D9', alpha=0.7)
                    ax.set_ylabel(metric)
                
                elif chart_type == "boxplot":
                    if len(metric_data) > 0:
                        bp = ax.boxplot(metric_data.values, patch_artist=True, tick_labels=[str(cat)])
                        bp['boxes'][0].set_facecolor('#4A90D9')
                        bp['boxes'][0].set_alpha(0.7)
                        ax.set_ylabel(metric)
                
                elif chart_type == "histograma":
                    if len(metric_data) > 0:
                        ax.hist(metric_data, bins=10, edgecolor='white', alpha=0.7, color='#4A90D9')
                        ax.set_xlabel(metric)
                        ax.set_ylabel("Frequência")
                
                ax.set_title(f"{cat} (n={len(metric_data)})")
            else:
                ax.text(0.5, 0.5, f"Campo '{metric}' não encontrado", ha='center', va='center')
                ax.set_title(str(cat))
        
        for i in range(n_cats, len(axes_flat)):
            axes_flat[i].axis('off')
        
        fig.tight_layout()
        
        self.current_fig = fig
        self._chart_figures.append(fig)
        return fig
    
    # ========== MÉTODOS DE CONVENIÊNCIA ==========
    
    def save_current(self, path: str, dpi: int = 150) -> bool:
        """Salva o gráfico atual em arquivo.
        
        Args:
            path: Caminho do arquivo (PNG, JPG, PDF, etc.)
            dpi: Resolução em pontos por polegada
        
        Retorna: True se salvo com sucesso
        """
        if self.current_fig is None:
            return False
        
        try:
            self.current_fig.savefig(path, dpi=dpi, bbox_inches='tight')
            return True
        except Exception:
            return False
    
    def save_all(self, base_path: str, dpi: int = 150) -> list[str]:
        """Salva todos os gráficos gerados nesta sessão.
        
        Args:
            base_path: Caminho base (sem extensão)
            dpi: Resolução
        
        Retorna: Lista de caminhos dos arquivos salvos
        """
        saved = []
        for i, fig in enumerate(self._chart_figures):
            path = f"{base_path}_{i+1}.png"
            try:
                fig.savefig(path, dpi=dpi, bbox_inches='tight')
                saved.append(path)
            except:
                pass
        return saved
    
    def clear(self) -> None:
        """Fecha todos os gráficos e limpa o histórico."""
        for fig in self._chart_figures:
            try:
                plt.close(fig)
            except:
                pass
        self._chart_figures = []
        self.current_fig = None
    
    def get_all_figures(self) -> list[Figure]:
        """Retorna todos os gráficos gerados nesta sessão."""
        return list(self._chart_figures)


def quick_chart(
    chart_type: str,
    df: pd.DataFrame,
    **kwargs
) -> Figure:
    """Função de conveniência para criar gráficos rapidamente.
    
    Uso:
        >>> from nav_charts import quick_chart
        >>> fig = quick_chart("boxplot", df, x="turma", y="percentual", title="Título")
    """
    charts = NavCharts(figsize=kwargs.pop('figsize', (10, 6)))
    
    chart_methods = {
        "barras": charts.boxplot,
        "linha": charts.linha,
        "linha_barra": charts.linha_barra,
        "boxplot": charts.boxplot,
        "scatter": charts.scatter,
        "heatmap": charts.heatmap,
        "comparativo": charts.comparativo,
    }
    
    method = chart_methods.get(chart_type.lower())
    if method:
        return method(df=df, **kwargs)
    else:
        fig, ax = plt.subplots(figsize=charts.figsize)
        ax.text(0.5, 0.5, f"Tipo de gráfico desconhecido: {chart_type}", ha='center', va='center')
        return fig


if __name__ == "__main__":
    print("=" * 60)
    print("NavCharts - Teste Rápido")
    print("=" * 60)
    
    import sys
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT = os.path.join(_SCRIPT_DIR, "..", "..")
    sys.path.insert(0, os.path.join(_PROJECT_ROOT, 'gui'))
    
    try:
        from nav_query import NavQuery
        
        nq = NavQuery()
        resultados_dir = os.path.join(_PROJECT_ROOT, "resultados")
        
        if os.path.exists(resultados_dir):
            print(f"\nCarregando dados de: {resultados_dir}")
            valid, errors = nq.load_directory(resultados_dir)
            print(f"Dados carregados: {valid} registros")
            
            if valid > 0:
                charts = NavCharts(nq, figsize=(8, 5))
                
                print("\nGerando gráficos de teste...")
                
                print("  1. Boxplot: % Acertos por Turma")
                fig1 = charts.boxplot(
                    x="preTest.turma",
                    y="testResults.correctPercent",
                    title="Distribuição de % Acertos por Turma"
                )
                
                print("  2. Scatter: Tempo de Reação vs % Acertos")
                fig2 = charts.scatter(
                    x="testResults.avgReactionTimeMs",
                    y="testResults.correctPercent",
                    hue="preTest.sexo",
                    title="Tempo de Reação vs % Acertos",
                    add_trendline=True
                )
                
                print("  3. Heatmap: Correlação")
                fig3 = charts.heatmap(
                    fields=["preTest.idade", "testResults.correctPercent", 
                           "testResults.correctCount", "testResults.avgReactionTimeMs"],
                    title="Matriz de Correlação"
                )
                
                output_dir = os.path.dirname(__file__)
                print(f"\nSalvando gráficos em: {output_dir}")
                
                paths = charts.save_all(os.path.join(output_dir, "teste_grafico"))
                for p in paths:
                    print(f"  Salvo: {p}")
                
                print("\n" + "=" * 60)
                print("TESTE CONCLUÍDO!")
                print("=" * 60)
            else:
                print("Nenhum dado carregado.")
        else:
            print(f"Diretório não encontrado: {resultados_dir}")
            
    except Exception as e:
        print(f"Erro no teste: {e}")
        import traceback
        traceback.print_exc()
