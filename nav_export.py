#!/usr/bin/env python3
"""
NAVINCLUD - Exportador de Resultados
Suporta: CSV, Excel (XLSX), TXT, PDF
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Optional, Any, Union
from pathlib import Path


try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class NavExport:
    """Exportador de resultados do NAVINCLUD.
    
    Formatos suportados:
        - CSV: Valores separados por vírgula
        - Excel (XLSX): Múltiplas abas
        - TXT: Relatório textual
        - PDF: Relatório com gráficos (se reportlab disponível)
    
    Uso:
        >>> from nav_export import NavExport
        >>> from nav_query import NavQuery
        >>> 
        >>> nq = NavQuery()
        >>> nq.load_directory("resultados/")
        >>> 
        >>> # Exportar DataFrame para CSV
        >>> NavExport.to_csv(nq.filtered_df, "dados.csv")
        >>> 
        >>> # Exportar múltiplos DataFrames para Excel
        >>> sheets = {
        ...     "DADOS_BRUTOS": nq.filtered_df,
        ...     "ESTATISTICAS": nq.describe_all_numeric()
        ... }
        >>> NavExport.to_excel(sheets, "relatorio.xlsx")
        >>> 
        >>> # Exportar análise completa
        >>> result, err = nq.groupby(["preTest.turma"], {"testId": ["count"]})
        >>> NavExport.export_full_analysis(
        ...     nq,
        ...     output_base="analise_completa",
        ...     formats=["csv", "xlsx"],
        ...     groupby_result=result
        ... )
    """
    
    @staticmethod
    def to_csv(
        df: pd.DataFrame,
        path: str,
        sep: str = ",",
        encoding: str = "utf-8-sig",
        index: bool = False
    ) -> tuple[bool, Optional[str]]:
        """Exporta DataFrame para CSV.
        
        Usa utf-8-sig para compatibilidade com Excel (acentos).
        
        Args:
            df: DataFrame a ser exportado
            path: Caminho do arquivo de saída
            sep: Separador de campos
            encoding: Codificação do arquivo
            index: Incluir índice do DataFrame
        
        Retorna: (sucesso, mensagem_erro)
        """
        if df is None or df.empty:
            return False, "DataFrame vazio ou None"
        
        try:
            df.to_csv(path, sep=sep, encoding=encoding, index=index)
            return True, None
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def to_excel(
        sheets_dict: dict[str, pd.DataFrame],
        path: str,
        include_index: bool = False
    ) -> tuple[bool, Optional[str]]:
        """Exporta múltiplos DataFrames como abas do Excel.
        
        Requer openpyxl instalado.
        
        Args:
            sheets_dict: Dicionário {"Nome_Aba": DataFrame, ...}
            path: Caminho do arquivo de saída
            include_index: Incluir índice dos DataFrames
        
        Retorna: (sucesso, mensagem_erro)
        """
        if not HAS_OPENPYXL:
            msg = "openpyxl não instalado. Execute: pip install openpyxl"
            return False, msg
        
        if not sheets_dict:
            return False, "Nenhum DataFrame fornecido"
        
        try:
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                for sheet_name, df in sheets_dict.items():
                    if df is None or df.empty:
                        continue
                    
                    safe_name = sheet_name[:31]
                    safe_name = safe_name.replace(':', '_').replace('\\', '_')
                    safe_name = safe_name.replace('?', '_').replace('*', '_')
                    safe_name = safe_name.replace('[', '_').replace(']', '_')
                    
                    df.to_excel(writer, sheet_name=safe_name, index=include_index)
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def to_txt(
        content: str,
        path: str,
        encoding: str = "utf-8-sig"
    ) -> tuple[bool, Optional[str]]:
        """Exporta texto para arquivo TXT.
        
        Args:
            content: Texto a ser exportado
            path: Caminho do arquivo de saída
            encoding: Codificação do arquivo
        
        Retorna: (sucesso, mensagem_erro)
        """
        try:
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            return True, None
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def generate_summary_text(
        df: pd.DataFrame,
        title: str = "Relatório NAVINCLUD",
        groupby_result: Optional[pd.DataFrame] = None
    ) -> str:
        """Gera relatório textual a partir de um DataFrame.
        
        Args:
            df: DataFrame com os dados
            title: Título do relatório
            groupby_result: Resultado opcional de groupby
        
        Retorna: String com o relatório formatado
        """
        lines = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        lines.append("=" * 80)
        lines.append(title.upper())
        lines.append("=" * 80)
        lines.append(f"Data: {now}")
        lines.append(f"Total de registros: {len(df) if not df.empty else 0}")
        lines.append("")
        
        if not df.empty:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                lines.append("-" * 80)
                lines.append("ESTATÍSTICAS DESCRITIVAS (CAMPOS NUMÉRICOS)")
                lines.append("-" * 80)
                
                stats = df[numeric_cols].describe().T
                lines.append(stats.to_string())
                lines.append("")
            
            object_cols = df.select_dtypes(include=['object', 'category']).columns
            for col in list(object_cols)[:10]:
                counts = df[col].value_counts(dropna=False)
                if len(counts) <= 20:
                    lines.append("-" * 80)
                    lines.append(f"DISTRIBUIÇÃO: {col}")
                    lines.append("-" * 80)
                    lines.append(counts.to_string())
                    lines.append("")
        
        if groupby_result is not None and not groupby_result.empty:
            lines.append("-" * 80)
            lines.append("RESULTADO DO AGRUPAMENTO")
            lines.append("-" * 80)
            lines.append(groupby_result.to_string(index=False))
            lines.append("")
        
        lines.append("=" * 80)
        lines.append("FIM DO RELATÓRIO")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    @staticmethod
    def export_full_analysis(
        nav_query: Any,
        output_base: str,
        formats: list[str] = ["csv", "xlsx"],
        groupby_result: Optional[pd.DataFrame] = None,
        timestamp: bool = True
    ) -> dict[str, str]:
        """Exporta análise completa em múltiplos formatos.
        
        Cria:
        - Dados brutos filtrados
        - Resultado do groupby (se fornecido)
        - Estatísticas descritivas
        - Configuração (filtros, campos derivados)
        
        Args:
            nav_query: Instância de NavQuery
            output_base: Nome base para os arquivos (sem extensão)
            formats: Lista de formatos: "csv", "xlsx", "txt", "pdf"
            groupby_result: Resultado opcional de groupby
            timestamp: Adicionar timestamp ao nome dos arquivos
        
        Retorna: Dicionário {"formato": "caminho_completo"}
        """
        results = {}
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S") if timestamp else ""
        suffix = f"_{ts}" if ts else ""
        
        df = nav_query.filtered_df if hasattr(nav_query, 'filtered_df') else pd.DataFrame()
        
        sheets_dict = {}
        if not df.empty:
            sheets_dict["DADOS_FILTRADOS"] = df
        
        if groupby_result is not None and not groupby_result.empty:
            sheets_dict["RESULTADO_GROUPBY"] = groupby_result
        
        if not df.empty:
            numeric = df.select_dtypes(include=['number'])
            if len(numeric.columns) > 0:
                stats = numeric.describe().T
                sheets_dict["ESTATISTICAS"] = stats
        
        try:
            config_data = {
                "filtros_ativos": [
                    {"campo": f.field, "operador": f.operator, "valor": str(f.value)}
                    for f in nav_query.get_active_filters()
                ] if hasattr(nav_query, 'get_active_filters') else [],
                "campos_derivados": list(nav_query.list_derived_fields().keys())
                if hasattr(nav_query, 'list_derived_fields') else [],
                "total_registros": len(df),
                "data_exportacao": ts
            }
            config_df = pd.DataFrame([config_data])
            sheets_dict["CONFIGURACAO"] = config_df
        except:
            pass
        
        output_dir = os.path.dirname(output_base) if os.path.dirname(output_base) else "."
        os.makedirs(output_dir, exist_ok=True)
        
        if "csv" in formats or "CSV" in formats:
            if not df.empty:
                csv_path = f"{output_base}_filtrados{suffix}.csv"
                success, err = NavExport.to_csv(df, csv_path)
                if success:
                    results["csv_dados"] = csv_path
            
            if groupby_result is not None and not groupby_result.empty:
                csv_groupby = f"{output_base}_groupby{suffix}.csv"
                success, err = NavExport.to_csv(groupby_result, csv_groupby)
                if success:
                    results["csv_groupby"] = csv_groupby
        
        if "xlsx" in formats or "XLSX" in formats:
            if sheets_dict:
                xlsx_path = f"{output_base}{suffix}.xlsx"
                success, err = NavExport.to_excel(sheets_dict, xlsx_path)
                if success:
                    results["xlsx"] = xlsx_path
                elif err:
                    results["xlsx_error"] = err
        
        if "txt" in formats or "TXT" in formats:
            txt_content = NavExport.generate_summary_text(
                df,
                title="Relatório NAVINCLUD",
                groupby_result=groupby_result
            )
            txt_path = f"{output_base}{suffix}.txt"
            success, err = NavExport.to_txt(txt_content, txt_path)
            if success:
                results["txt"] = txt_path
        
        if "pdf" in formats or "PDF" in formats:
            if HAS_REPORTLAB and not df.empty:
                txt_content = NavExport.generate_summary_text(
                    df,
                    title="Relatório NAVINCLUD",
                    groupby_result=groupby_result
                )
                pdf_path = f"{output_base}{suffix}.pdf"
                success, err = NavExport._simple_pdf(txt_content, pdf_path)
                if success:
                    results["pdf"] = pdf_path
                elif err:
                    results["pdf_error"] = err
        
        return results
    
    @staticmethod
    def _simple_pdf(
        text: str,
        path: str,
        title: str = "Relatório NAVINCLUD"
    ) -> tuple[bool, Optional[str]]:
        """Gera PDF simples a partir de texto.
        
        Versão simplificada para casos básicos.
        Para PDFs com gráficos, use a classe ExportEngine da GUI.
        """
        if not HAS_REPORTLAB:
            return False, "reportlab não instalado"
        
        try:
            font_path = None
            for candidate in ['DejaVuSans.ttf', 
                             'C:/Windows/Fonts/ARIALUNI.TTF',
                             'C:/Windows/Fonts/SEGOEUI.TTF',
                             'C:/Windows/Fonts/arial.ttf']:
                if os.path.exists(candidate):
                    font_path = candidate
                    break
            
            c = canvas.Canvas(path, pagesize=A4)
            width, height = A4
            
            if font_path:
                try:
                    pdfmetrics.registerFont(TTFont('AppFont', font_path))
                    font_name = 'AppFont'
                except:
                    font_name = 'Helvetica'
            else:
                font_name = 'Helvetica'
            
            y = height - 50
            
            c.setFont(font_name, 20)
            c.drawString(30, y, title)
            y -= 30
            
            c.setFont(font_name, 10)
            c.drawString(30, y, f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            y -= 30
            
            lines = text.split('\n')
            line_height = 14
            
            c.setFont(font_name, 10)
            
            for line in lines:
                if y < 50:
                    c.showPage()
                    y = height - 50
                    c.setFont(font_name, 10)
                
                c.drawString(30, y, line[:120])
                y -= line_height
            
            c.save()
            return True, None
            
        except Exception as e:
            return False, str(e)


def quick_export(
    nav_query: Any,
    output_name: str = "analise_navinclud",
    formats: list[str] = ["csv", "xlsx", "txt"]
) -> dict[str, str]:
    """Função de conveniência para exportação rápida.
    
    Uso:
        >>> from nav_export import quick_export
        >>> results = quick_export(nq, "minha_analise", ["csv", "xlsx"])
    """
    return NavExport.export_full_analysis(
        nav_query=nav_query,
        output_base=output_name,
        formats=formats,
        timestamp=True
    )


if __name__ == "__main__":
    print("=" * 60)
    print("NavExport - Teste Rápido")
    print("=" * 60)
    
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gui'))
    
    try:
        from nav_query import NavQuery
        
        nq = NavQuery()
        resultados_dir = os.path.join(os.path.dirname(__file__), "resultados")
        
        if os.path.exists(resultados_dir):
            print(f"\nCarregando dados de: {resultados_dir}")
            valid, errors = nq.load_directory(resultados_dir)
            print(f"Dados carregados: {valid} registros")
            
            if valid > 0:
                output_base = os.path.join(os.path.dirname(__file__), "teste_export")
                
                print(f"\nExportando para: {output_base}")
                results = quick_export(nq, output_base, ["csv", "xlsx", "txt"])
                
                print("\nArquivos gerados:")
                for fmt, path in results.items():
                    print(f"  {fmt}: {path}")
                
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
