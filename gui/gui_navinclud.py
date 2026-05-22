import os
import json
import threading
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from nav_data import NavData
from field_discovery import FieldDiscoverer

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('green')

CARD_COLORS = {
    'total': '#4A90D9',
    'normal': '#27AE60',
    'deficiente': '#E74C3C',
    'maquinas': '#F39C12',
    'media': '#9B59B6',
}


class ExportEngine:
    @staticmethod
    def export_txt(data: NavData, group_fields, agg_fields, filepath):
        lines = []
        lines.append('=' * 80)
        lines.append('NAVINCLUD - RELATORIO DE TESTES')
        lines.append(f'Data: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}')
        dirs = data.directories or ['N/A']
        lines.append(f'Diretorios: {len(dirs)}')
        for d in dirs:
            meta = data.metadata.get(d, {})
            lines.append(f'  {d}: {meta.get("valid", 0)} testes validos')
        lines.append('=' * 80)
        lines.append('')

        summary = data.get_summary_stats()
        lines.append(f'Total de testadores: {summary["total"]}')
        lines.append(f'Normais (>=90%): {summary["normal_count"]}')
        lines.append(f'Deficientes (<90%): {summary["deficient_count"]}')
        lines.append(f'Maquinas: {summary["terminal_count"]}')
        lines.append(f'Media de acertos: {summary["avg_percent"]}%')
        lines.append('')

        if group_fields or agg_fields:
            lines.append('--- RESULTADOS DO DASHBOARD ---')
            lines.append(f'Agrupar por: {group_fields or "(nenhum)"}')
            lines.append(f'Agregar: {agg_fields or "(nenhum)"}')
            lines.append('')
            result, error = data.groupby_dynamic(group_fields, agg_fields)
            if result is not None and not result.empty:
                lines.append(result.to_string(index=False))
            else:
                lines.append(error or 'Nenhum resultado.')
            lines.append('')
        else:
            lines.append('(Nenhum campo selecionado no dashboard)')
            lines.append('')

        lines.append('=' * 80)
        lines.append('Graficos nao disponiveis em TXT.')
        lines.append('FIM DO RELATORIO')
        lines.append('=' * 80)

        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write('\n'.join(lines))

    @staticmethod
    def export_pdf(data: NavData, group_fields, agg_fields, filepath,
                   chart_images=None):
        font_path = None
        for candidate in ['DejaVuSans.ttf', 'C:/Windows/Fonts/ARIALUNI.TTF',
                          'C:/Windows/Fonts/SEGOEUI.TTF']:
            if os.path.exists(candidate):
                font_path = candidate
                break

        if font_path:
            pdfmetrics.registerFont(TTFont('AppFont', font_path))
            font_name = 'AppFont'
        else:
            font_name = 'Helvetica'

        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4

        c.setFont(font_name, 24)
        c.drawString(30, height - 50, 'NAVINCLUD - Relatorio de Testes')
        c.setFont(font_name, 12)
        c.drawString(30, height - 70, f'Data: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}')
        c.drawString(30, height - 85, f'Diretorios carregados: {len(data.directories)}')

        summary = data.get_summary_stats()
        y = height - 110
        c.setFont(font_name, 14)
        c.drawString(30, y, 'Resumo:')
        c.setFont(font_name, 11)
        y -= 18
        for key, val in [('Total', summary['total']),
                         ('Normais', summary['normal_count']),
                         ('Deficientes', summary['deficient_count']),
                         ('Maquinas', summary['terminal_count']),
                         ('Media %', summary['avg_percent'])]:
            c.drawString(40, y, f'{key}: {val}')
            y -= 15

        result, error = data.groupby_dynamic(group_fields, agg_fields)
        if result is not None and not result.empty:
            y -= 20
            c.setFont(font_name, 14)
            c.drawString(30, y, 'Tabela de Resultados:')
            y -= 18
            c.setFont(font_name, 8)
            col_widths = [max(50, 8 * len(str(col))) for col in result.columns]
            for i, col in enumerate(result.columns):
                c.drawString(30 + sum(col_widths[:i]), y, str(col)[:15])
            y -= 12
            c.setFont(font_name, 7)
            for _, row in result.iterrows():
                if y < 50:
                    c.showPage()
                    y = height - 50
                    c.setFont(font_name, 7)
                for i, val in enumerate(row):
                    c.drawString(30 + sum(col_widths[:i]), y, str(val)[:12])
                y -= 10

        if chart_images:
            for img_path in chart_images:
                if os.path.exists(img_path):
                    c.showPage()
                    c.setFont(font_name, 12)
                    c.drawString(30, height - 30, 'Grafico:')
                    try:
                        c.drawImage(img_path, 30, height - 500,
                                    width=landscape(A4)[0] - 60,
                                    height=400, preserveAspectRatio=True)
                    except Exception:
                        c.drawString(30, height - 100, '(Erro ao renderizar grafico)')

        c.save()

    @staticmethod
    def export_pdf_with_charts(data, group_fields, agg_fields, filepath,
                                figures):
        temp_dir = os.path.join(os.path.dirname(filepath), '.navinclud_charts')
        os.makedirs(temp_dir, exist_ok=True)
        chart_paths = []
        for i, fig in enumerate(figures):
            path = os.path.join(temp_dir, f'chart_{i}.png')
            fig.savefig(path, dpi=150, bbox_inches='tight')
            chart_paths.append(path)

        ExportEngine.export_pdf(data, group_fields, agg_fields, filepath,
                                chart_images=chart_paths)

        for p in chart_paths:
            try:
                os.remove(p)
            except Exception:
                pass
        try:
            os.rmdir(temp_dir)
        except Exception:
            pass


class DashboardFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, nav_data, **kwargs):
        super().__init__(master, **kwargs)
        self.nav_data = nav_data
        self.selected_groups = []
        self.selected_aggs = []
        self.current_chart_type = 'barras'
        self.current_figure = None
        self.current_canvas = None
        self._calculating = False
        self._chart_figures = []

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_control_panel()
        self._build_summary_cards()
        self._build_tab_view()

    def _build_control_panel(self):
        panel = ctk.CTkFrame(self, width=280, corner_radius=8)
        panel.grid(row=0, column=0, rowspan=3, sticky='nsw', padx=5, pady=5)
        panel.grid_propagate(False)

        ctk.CTkLabel(panel, text='Painel de Controle',
                     font=('Arial', 16, 'bold')).pack(pady=(10, 5))

        self._ctrl_vars = {}
        field_categories = self.nav_data.get_fields_by_category()
        all_active = self.nav_data.get_active_field_keys()

        for cat_name, cat_fields in field_categories.items():
            active = [f for f in cat_fields if f in all_active]
            if not active:
                continue

            frame = ctk.CTkFrame(panel, corner_radius=4)
            frame.pack(fill='x', padx=5, pady=2)

            row = ctk.CTkFrame(frame, fg_color='transparent')
            row.pack(fill='x')
            ctk.CTkLabel(row, text=cat_name, font=('Arial', 12, 'bold'),
                         anchor='w').pack(side='left', padx=5)

            def make_toggle(cat=cat_name, flds=active):
                def toggle():
                    all_checked = all(
                        self._ctrl_vars.get(f, ctk.BooleanVar()).get() for f in flds
                    )
                    new_val = not all_checked
                    for f in flds:
                        if f in self._ctrl_vars:
                            self._ctrl_vars[f].set(new_val)
                return toggle

            ctk.CTkButton(row, text='T', width=24, height=20,
                          command=make_toggle(cat_name, active),
                          font=('Arial', 9)).pack(side='right', padx=2)

            for field in active:
                display = FieldDiscoverer.get_display_name(field)
                var = ctk.BooleanVar(value=False)
                self._ctrl_vars[field] = var
                cb = ctk.CTkCheckBox(frame, text=display, variable=var,
                                     font=('Arial', 10))
                cb.pack(anchor='w', padx=15, pady=1)

        ctk.CTkLabel(panel, text='Tipo de Grafico:',
                     font=('Arial', 12)).pack(pady=(10, 2))
        self._chart_combo = ctk.CTkComboBox(
            panel, values=['Barras', 'Pizza', 'Histograma', 'Composto'],
            command=self._on_chart_type_change, width=200)
        self._chart_combo.set('Barras')
        self._chart_combo.pack(pady=(0, 10))

        btn_frame = ctk.CTkFrame(panel, fg_color='transparent')
        btn_frame.pack(fill='x', padx=5, pady=5)
        ctk.CTkButton(btn_frame, text='Recalcular',
                      command=self._on_recalculate).pack(fill='x', pady=2)
        ctk.CTkButton(btn_frame, text='Redesenhar',
                      command=self._on_redraw).pack(fill='x', pady=2)
        ctk.CTkButton(btn_frame, text='Exportar',
                      command=self._on_export).pack(fill='x', pady=2)

    def _build_summary_cards(self):
        card_frame = ctk.CTkFrame(self, corner_radius=8)
        card_frame.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        stats = self.nav_data.get_summary_stats()

        self._card_labels = {}
        items = [
            ('total', f'Total: {stats["total"]}', CARD_COLORS['total']),
            ('normal', f'Normais: {stats["normal_count"]}', CARD_COLORS['normal']),
            ('deficiente', f'Deficientes: {stats["deficient_count"]}', CARD_COLORS['deficiente']),
            ('maquinas', f'Maquinas: {stats["terminal_count"]}', CARD_COLORS['maquinas']),
            ('media', f'Media: {stats["avg_percent"]}%', CARD_COLORS['media']),
        ]
        for i, (key, text, color) in enumerate(items):
            c = ctk.CTkFrame(card_frame, fg_color=color, corner_radius=6,
                             width=150, height=60)
            c.grid(row=0, column=i, padx=4, pady=5, sticky='ew')
            c.grid_propagate(False)
            lbl = ctk.CTkLabel(c, text=text, font=('Arial', 14, 'bold'),
                               text_color='white')
            lbl.place(relx=0.5, rely=0.5, anchor='center')
            self._card_labels[key] = lbl
        card_frame.grid_columnconfigure(tuple(range(5)), weight=1)

    def _build_tab_view(self):
        self._tab_view = ctk.CTkTabview(self, corner_radius=8)
        self._tab_view.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._table_tab = self._tab_view.add('Tabela')
        self._bar_tab = self._tab_view.add('Barras')
        self._pie_tab = self._tab_view.add('Pizza')
        self._hist_tab = self._tab_view.add('Histograma')
        self._compound_tab = self._tab_view.add('Composto')

        for tab in [self._table_tab, self._bar_tab, self._pie_tab,
                    self._hist_tab, self._compound_tab]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

        self._tree_frame = ctk.CTkFrame(self._table_tab)
        self._tree_frame.grid(row=0, column=0, sticky='nsew')
        self._tree_frame.grid_rowconfigure(0, weight=1)
        self._tree_frame.grid_columnconfigure(0, weight=1)

        self._chart_frames = {}
        for tab_name in ['Barras', 'Pizza', 'Histograma', 'Composto']:
            tab_widget = getattr(self, f'_{tab_name.lower()}_tab', None)
            if tab_widget:
                f = ctk.CTkFrame(tab_widget)
                f.grid(row=0, column=0, sticky='nsew')
                f.grid_rowconfigure(0, weight=1)
                f.grid_columnconfigure(0, weight=1)
                self._chart_frames[tab_name] = f

        self._show_empty_message(self._table_tab, 'Clique em [Recalcular] para gerar resultados.')

    def _show_empty_message(self, parent, text):
        for w in parent.winfo_children():
            w.destroy()
        lbl = ctk.CTkLabel(parent, text=text, font=('Arial', 14))
        lbl.place(relx=0.5, rely=0.5, anchor='center')

    def _gather_selections(self):
        groups = []
        aggs = []
        for field, var in self._ctrl_vars.items():
            if not var.get():
                continue
            categories = self.nav_data.categorized
            if field in categories.get('categoricos', []) or field in categories.get('booleanos', []):
                groups.append(field)
            elif field in categories.get('numericos', []):
                aggs.append(field)
            elif field in categories.get('arrays', []):
                groups.append(field)
        return groups, aggs

    def _on_chart_type_change(self, choice):
        mapping = {'Barras': 'barras', 'Pizza': 'pizza',
                   'Histograma': 'histograma', 'Composto': 'composto'}
        self.current_chart_type = mapping.get(choice, 'barras')

    def _on_recalculate(self):
        if self._calculating:
            return
        self._calculating = True

        groups, aggs = self._gather_selections()
        self.selected_groups = groups
        self.selected_aggs = aggs

        result, error = self.nav_data.groupby_dynamic(groups, aggs)

        if error:
            self._show_empty_message(self._table_tab, error)
            self._calculating = False
            return

        self._display_table(result)
        self._on_redraw()
        self._calculating = False

    def _on_redraw(self):
        groups, aggs = self._gather_selections()
        result, _ = self.nav_data.groupby_dynamic(groups, aggs)
        if result is None or result.empty:
            return

        chart_type = self.current_chart_type

        if chart_type == 'composto':
            self._draw_compound_chart(result, groups, aggs)
        elif chart_type == 'pizza':
            self._draw_pie_chart(result, groups, aggs)
        elif chart_type == 'histograma':
            self._draw_histogram(result, groups, aggs)
        else:
            self._draw_bar_chart(result, groups, aggs)

    def _display_table(self, result):
        for w in self._tree_frame.winfo_children():
            w.destroy()

        if result is None or result.empty:
            self._show_empty_message(self._tree_frame, 'Nenhum resultado.')
            return

        tree = ttk.Treeview(self._tree_frame, show='headings',
                            style='Treeview')
        vsb = ttk.Scrollbar(self._tree_frame, orient='vertical', command=tree.yview)
        hsb = ttk.Scrollbar(self._tree_frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        cols = list(result.columns)
        tree['columns'] = cols
        for col in cols:
            tree.heading(col, text=col)
            max_w = max(80, 10 * len(str(col)))
            tree.column(col, width=min(max_w, 200), minwidth=60)

        for _, row in result.iterrows():
            values = [str(v) if not isinstance(v, float) else f'{v:.2f}'
                      for v in row]
            tree.insert('', 'end', values=values)

        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        self._tree_frame.grid_rowconfigure(0, weight=1)
        self._tree_frame.grid_columnconfigure(0, weight=1)

    def _clear_chart_tab(self, tab_name):
        f = self._chart_frames.get(tab_name)
        if not f:
            return
        for w in f.winfo_children():
            w.destroy()

    def _embed_chart(self, tab_name, fig):
        self._clear_chart_tab(tab_name)
        f = self._chart_frames.get(tab_name)
        if not f:
            return

        if self.current_canvas:
            try:
                self.current_canvas.get_tk_widget().destroy()
            except Exception:
                pass
        if self.current_figure:
            try:
                plt.close(self.current_figure)
            except Exception:
                pass
            self.current_figure = None

        canvas_widget = FigureCanvasTkAgg(fig, master=f)
        canvas_widget.draw()
        canvas_widget.get_tk_widget().pack(fill='both', expand=True)

        self.current_figure = fig
        self.current_canvas = canvas_widget
        self._chart_figures.append(fig)

    def _draw_bar_chart(self, result, groups, aggs):
        import matplotlib.pyplot as plt
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)

        numeric_cols = [c for c in result.columns if c.endswith('_mean')
                        or c == 'count' or (aggs and any(a in c for a in aggs))]
        label_cols = [c for c in result.columns if c not in numeric_cols]

        if label_cols:
            labels = result[label_cols[0]].astype(str) if label_cols else result.index.astype(str)
        else:
            labels = result.index.astype(str)

        plot_cols = numeric_cols[:3]
        data = result[plot_cols] if plot_cols else result.select_dtypes(include='number')

        if data.empty:
            ax.text(0.5, 0.5, 'Sem dados numericos', ha='center', va='center')
        else:
            x = range(len(data))
            for i, col in enumerate(data.columns[:3]):
                ax.bar([p + i * 0.25 for p in x], data[col],
                       width=0.2, label=str(col)[:15])
            ax.set_xticks([p + 0.25 for p in x])
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
            ax.legend(fontsize=8)
            fig.tight_layout()

        self._embed_chart('Barras', fig)

    def _draw_pie_chart(self, result, groups, aggs):
        import matplotlib.pyplot as plt
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)

        label_col = result.columns[0] if len(result.columns) > 0 else None
        count_col = 'count' if 'count' in result.columns else (
            result.columns[-1] if len(result.columns) > 1 else None
        )

        if label_col and count_col and count_col in result.columns:
            sizes = result[count_col]
            labels = result[label_col].astype(str)
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
        else:
            ax.text(0.5, 0.5, 'Dados nao suportam grafico de pizza',
                    ha='center', va='center')
        fig.tight_layout()
        self._embed_chart('Pizza', fig)

    def _draw_histogram(self, result, groups, aggs):
        import matplotlib.pyplot as plt
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)

        numeric_cols = result.select_dtypes(include='number').columns[:2]
        if len(numeric_cols) > 0 and numeric_cols[0] in result.columns:
            ax.hist(result[numeric_cols[0]].dropna(), bins=10, edgecolor='white')
            ax.set_xlabel(str(numeric_cols[0]))
            ax.set_ylabel('Frequencia')
        else:
            ax.text(0.5, 0.5, 'Sem dados numericos para histograma',
                    ha='center', va='center')
        fig.tight_layout()
        self._embed_chart('Histograma', fig)

    def _draw_compound_chart(self, result, groups, aggs):
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 2, figsize=(8, 6), dpi=100)
        fig.tight_layout(pad=3.0)

        numeric_cols = result.select_dtypes(include='number').columns
        label_cols = [c for c in result.columns if c not in numeric_cols]
        labels = result[label_cols[0]].astype(str) if label_cols else []

        axes_flat = axes.flatten()

        if len(numeric_cols) > 0 and len(labels) > 0:
            ax = axes_flat[0]
            col = numeric_cols[0]
            ax.bar(labels, result[col])
            ax.set_title(str(col)[:20])
            ax.tick_params(axis='x', rotation=45, labelsize=7)
        else:
            axes_flat[0].text(0.5, 0.5, 'Sem dados', ha='center', va='center')

        if len(numeric_cols) > 1 and len(labels) > 0:
            ax = axes_flat[1]
            col = numeric_cols[1]
            ax.bar(labels, result[col])
            ax.set_title(str(col)[:20])
            ax.tick_params(axis='x', rotation=45, labelsize=7)
        else:
            axes_flat[1].text(0.5, 0.5, 'Sem dados', ha='center', va='center')

        if len(numeric_cols) > 2 and len(labels) > 0:
            ax = axes_flat[2]
            col = numeric_cols[2]
            ax.pie(result[col], labels=labels, autopct='%1.0f%%')
            ax.set_title(str(col)[:20])
        else:
            if len(numeric_cols) > 0:
                ax = axes_flat[2]
                ax.hist(result[numeric_cols[0]].dropna(), bins=8)
                ax.set_title('Histograma')
            else:
                axes_flat[2].text(0.5, 0.5, 'Sem dados', ha='center', va='center')

        axes_flat[3].axis('off')
        axes_flat[3].text(0.5, 0.5,
                          f'Grupos: {groups[:3]}\nAgreg: {aggs[:3]}',
                          ha='center', va='center', fontsize=9)

        self._embed_chart('Composto', fig)

    def _on_export(self):
        dialog = ctk.CTkInputDialog(
            text='Escolha o formato:\n1 - TXT\n2 - PDF\n3 - Ambos',
            title='Exportar Resultados')
        choice = dialog.get_input()

        if choice not in ('1', '2', '3'):
            return

        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')

        if choice in ('1', '3'):
            path = filedialog.asksaveasfilename(
                defaultextension='.txt',
                filetypes=[('Arquivo TXT', '*.txt')],
                initialfile=f'navinclud_relatorio_{timestamp}.txt')
            if path:
                ExportEngine.export_txt(
                    self.nav_data, self.selected_groups,
                    self.selected_aggs, path)
                messagebox.showinfo('Sucesso', f'TXT salvo em:\n{path}')

        if choice in ('2', '3'):
            path = filedialog.asksaveasfilename(
                defaultextension='.pdf',
                filetypes=[('Arquivo PDF', '*.pdf')],
                initialfile=f'navinclud_relatorio_{timestamp}.pdf')
            if path:
                ExportEngine.export_pdf_with_charts(
                    self.nav_data, self.selected_groups,
                    self.selected_aggs, path, self._chart_figures)
                messagebox.showinfo('Sucesso', f'PDF salvo em:\n{path}')


class NavincludApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('NAVINCLUD - Analise de Testes de Visao de Cores')
        self.minsize(1280, 720)
        self.resizable(True, True)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.nav_data = NavData()
        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=0, column=0, sticky='nsew')
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self._show_welcome()

    def _clear(self):
        for w in self.main_container.winfo_children():
            w.destroy()

    def _show_welcome(self):
        self._clear()
        frame = ctk.CTkFrame(self.main_container)
        frame.place(relx=0.5, rely=0.5, anchor='center')

        ctk.CTkLabel(frame, text='NAVINCLUD',
                     font=('Arial', 48, 'bold')).pack(pady=(30, 5))
        ctk.CTkLabel(frame, text='Analise de Testes de Visao de Cores',
                     font=('Arial', 18)).pack(pady=(0, 20))
        ctk.CTkLabel(frame, text='Teste de Ishihara - Agregador de Resultados',
                     font=('Arial', 12)).pack(pady=(0, 30))
        ctk.CTkButton(frame, text='▶ Iniciar', width=200, height=50,
                      font=('Arial', 16),
                      command=self._show_load).pack(pady=(0, 30))

    def _show_load(self):
        self._clear()
        frame = ctk.CTkFrame(self.main_container)
        frame.place(relx=0.5, rely=0.5, anchor='center')

        ctk.CTkLabel(frame, text='Selecionar Pasta com Resultados',
                     font=('Arial', 18)).pack(pady=(20, 10))
        ctk.CTkLabel(frame, text='Escolha uma pasta contendo arquivos navinclud_*.json',
                     font=('Arial', 12)).pack(pady=(0, 15))

        self._progress = ctk.CTkProgressBar(frame, width=300)
        self._progress.pack(pady=10)
        self._progress.set(0)

        self._status_label = ctk.CTkLabel(frame, text='')
        self._status_label.pack(pady=5)

        btn_frame = ctk.CTkFrame(frame, fg_color='transparent')
        btn_frame.pack(pady=15)

        ctk.CTkButton(btn_frame, text='Selecionar Pasta',
                      command=self._do_load).pack(side='left', padx=5)
        ctk.CTkButton(btn_frame, text='Voltar',
                      command=self._show_welcome).pack(side='left', padx=5)

    def _do_load(self):
        directory = filedialog.askdirectory(title='Selecione a pasta com resultados JSON')
        if not directory:
            return

        self._status_label.configure(text='Carregando...')
        self._progress.set(0)

        def update_progress(current, total):
            def _update():
                self._progress.set(current / total if total > 0 else 0)
                self._status_label.configure(
                    text=f'Processando {current}/{total}')
            self.after(0, _update)

        def load_thread():
            try:
                valid, errors = self.nav_data.load_directory(
                    directory, progress_callback=update_progress)
                self.after(0, lambda: self._on_load_complete(valid, errors, directory))
            except Exception as e:
                self.after(0, lambda: self._status_label.configure(
                    text=f'Erro: {str(e)}'))

        t = threading.Thread(target=load_thread, daemon=True)
        t.start()

    def _on_load_complete(self, valid, errors, directory):
        if valid == 0:
            self._status_label.configure(
                text=f'Nenhum JSON valido encontrado em:\n{directory}')
            return
        self._status_label.configure(
            text=f'{valid} testes carregados, {errors} ignorados.')
        self.after(800, self._show_menu)

    def _show_menu(self):
        self._clear()
        frame = ctk.CTkFrame(self.main_container)
        frame.place(relx=0.5, rely=0.5, anchor='center')

        summary = self.nav_data.get_summary_stats()
        ctk.CTkLabel(frame, text='Menu Pos-Processamento',
                     font=('Arial', 24, 'bold')).pack(pady=(20, 5))
        ctk.CTkLabel(frame, text=f'Dados carregados: {summary["total"]} testes',
                     font=('Arial', 14)).pack(pady=(0, 20))

        card_frame = ctk.CTkFrame(frame, fg_color='transparent')
        card_frame.pack(pady=10)

        cards = [
            ('📂', 'CARREGAR PROXIMA\nSEQUENCIA', 'Acumular mais dados de\noutra pasta', self._show_load),
            ('📊', 'DASHBOARD\nCOMPLETO', 'Analisar dados com\ngraficos e tabelas', self._show_dashboard),
            ('📄', 'IMPRIMIR\nRESULTADOS', 'Exportar relatorio\nem TXT ou PDF', self._show_export_menu),
        ]
        for i, (icon, title, desc, cmd) in enumerate(cards):
            c = ctk.CTkFrame(card_frame, corner_radius=8, width=220, height=180)
            c.grid(row=0, column=i, padx=10, pady=10)
            c.grid_propagate(False)
            ctk.CTkLabel(c, text=icon, font=('Arial', 32)).pack(pady=(15, 5))
            ctk.CTkLabel(c, text=title, font=('Arial', 14, 'bold')).pack()
            ctk.CTkLabel(c, text=desc, font=('Arial', 10),
                         text_color='gray').pack(pady=5)
            ctk.CTkButton(c, text='Abrir', command=cmd).pack(pady=10)
            ctk.CTkButton(c, text='Sair', command=self._on_exit,
                          fg_color='transparent', border_width=1,
                          font=('Arial', 10)).pack(pady=2)

    def _show_dashboard(self):
        self._clear()
        dashboard = DashboardFrame(self.main_container, self.nav_data)
        dashboard.grid(row=0, column=0, sticky='nsew')

        btn_frame = ctk.CTkFrame(dashboard, fg_color='transparent')
        btn_frame.grid(row=2, column=1, sticky='e', padx=5, pady=5)
        ctk.CTkButton(btn_frame, text='← Voltar ao Menu',
                      command=self._show_menu).pack(side='right', padx=5)

    def _show_export_menu(self):
        self._clear()
        frame = ctk.CTkFrame(self.main_container)
        frame.place(relx=0.5, rely=0.5, anchor='center')

        summary = self.nav_data.get_summary_stats()
        ctk.CTkLabel(frame, text='Exportar Resultados',
                     font=('Arial', 24, 'bold')).pack(pady=(20, 10))
        ctk.CTkLabel(frame, text=f'{summary["total"]} testes carregados',
                     font=('Arial', 14)).pack(pady=(0, 10))

        ctk.CTkLabel(frame, text='Escolha o formato de exportacao:',
                     font=('Arial', 12)).pack(pady=10)

        def do_export_txt():
            path = filedialog.asksaveasfilename(
                defaultextension='.txt',
                filetypes=[('Arquivo TXT', '*.txt')],
                initialfile=f'navinclud_relatorio.txt')
            if path:
                ExportEngine.export_txt(self.nav_data, [], [], path)
                messagebox.showinfo('Sucesso', f'TXT salvo em:\n{path}')

        def do_export_pdf():
            path = filedialog.asksaveasfilename(
                defaultextension='.pdf',
                filetypes=[('Arquivo PDF', '*.pdf')],
                initialfile=f'navinclud_relatorio.pdf')
            if path:
                ExportEngine.export_pdf(self.nav_data, [], [], path)
                messagebox.showinfo('Sucesso', f'PDF salvo em:\n{path}')

        btn_frame = ctk.CTkFrame(frame, fg_color='transparent')
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text='Exportar TXT',
                      command=do_export_txt).pack(side='left', padx=5)
        ctk.CTkButton(btn_frame, text='Exportar PDF',
                      command=do_export_pdf).pack(side='left', padx=5)
        ctk.CTkButton(btn_frame, text='Voltar',
                      command=self._show_menu).pack(side='left', padx=5)

    def _on_exit(self):
        self.destroy()


if __name__ == '__main__':
    app = NavincludApp()
    app.mainloop()
