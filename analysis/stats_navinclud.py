#!/usr/bin/env python3
"""
NAVINCLUD - Geracao de Estatisticas e Graficos
Le o JSON agregado, oferece selecao interativa de campos,
gera graficos (matplotlib/seaborn) e relatorios .md.

Uso:
  python stats_navinclud.py
  python stats_navinclud.py --json export/navinclud_agregado.json
  python stats_navinclud.py --auto --fields turma,sexo,idade --output ambos
"""

import os, sys, json, argparse
from collections import Counter, defaultdict
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

sns.set_theme(style='whitegrid')

# ── HELPERS ────────────────────────────────────────────────────

def safe_print(text, **kwargs):
    try:
        print(text, **kwargs)
    except UnicodeEncodeError:
        safe_text = text.encode('cp1252', errors='replace').decode('cp1252')
        print(safe_text, **kwargs)


def load_alunos(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'alunos' in data:
        return data['alunos']
    if isinstance(data, list):
        return data
    raise ValueError('Formato JSON nao reconhecido')


# ── FIELD EXTRACTION ───────────────────────────────────────────

def extract_fields(alunos):
    fields = {}
    a0 = alunos[0]

    # Simple top-level fields
    for k in ('terminalId', 'testId', 'timestamp', 'positivity'):
        ftype = 'categorical'
        if k == 'timestamp':
            ftype = 'datetime'
        values = [a.get(k) for a in alunos if a.get(k) is not None]
        if values:
            fields[k] = {'type': ftype, 'values': values, 'label': k, 'source': 'root'}

    # preTest fields
    pre_keys = ['turma', 'turma_normalized', 'turma_original', 'sexo', 'idade']
    for k in pre_keys:
        values = [a.get('preTest', {}).get(k) for a in alunos if a.get('preTest', {}).get(k) is not None]
        if values:
            is_num = isinstance(values[0], (int, float))
            fields[f'preTest.{k}'] = {
                'type': 'numerical' if is_num else 'categorical',
                'values': values,
                'label': k,
                'source': 'preTest',
            }

    # testResults fields
    tr_keys_flat = ['correctCount', 'correctPercent', 'totalPlates',
                    'avgReactionTimeMs', 'controlPlateErrors']
    for k in tr_keys_flat:
        values = [a.get('testResults', {}).get(k) for a in alunos]
        values = [v for v in values if v is not None]
        if values:
            fields[f'testResults.{k}'] = {
                'type': 'numerical',
                'values': values,
                'label': k,
                'source': 'testResults',
            }

    # detectedDefect
    values = [a.get('testResults', {}).get('detectedDefect', 'none') for a in alunos]
    values = [v if v and v != 'none' else 'normal' for v in values]
    fields['testResults.detectedDefect'] = {
        'type': 'categorical',
        'values': values,
        'label': 'detectedDefect',
        'source': 'testResults',
    }

    # Errors by type
    all_error_types = set()
    for a in alunos:
        all_error_types.update(a.get('testResults', {}).get('errorsByType', {}).keys())
    for etype in sorted(all_error_types):
        values = []
        for a in alunos:
            v = a.get('testResults', {}).get('errorsByType', {}).get(etype, 0)
            values.append(v)
        fields[f'errors.{etype}'] = {
            'type': 'numerical',
            'values': values,
            'label': f'error_{etype}',
            'source': 'errorsByType',
        }

    # Score by type
    all_score_types = set()
    for a in alunos:
        all_score_types.update(a.get('testResults', {}).get('scorePointsByType', {}).keys())
    for stype in sorted(all_score_types):
        values = []
        for a in alunos:
            v = a.get('testResults', {}).get('scorePointsByType', {}).get(stype, 0)
            values.append(v)
        fields[f'scores.{stype}'] = {
            'type': 'numerical',
            'values': values,
            'label': f'score_{stype}',
            'source': 'scorePointsByType',
        }

    # Perception (multi-select - one-hot)
    all_perceptions = set()
    for a in alunos:
        all_perceptions.update(a.get('testResults', {}).get('testPerception', []))
    for perc in sorted(all_perceptions):
        values = [1 if perc in a.get('testResults', {}).get('testPerception', []) else 0 for a in alunos]
        fields[f'perception.{perc}'] = {
            'type': 'binary',
            'values': values,
            'label': f'perception_{perc}',
            'source': 'testPerception',
        }

    # normalPostTest
    normal_avail = sum(1 for a in alunos if a.get('normalPostTest'))
    if normal_avail:
        npt_keys = set()
        for a in alunos:
            if a.get('normalPostTest'):
                npt_keys.update(a['normalPostTest'].keys())
        for k in sorted(npt_keys):
            values = [a.get('normalPostTest', {}).get(k, '') for a in alunos]
            str_values = [str(v) if v is not None else '' for v in values]
            fields[f'normalPostTest.{k}'] = {
                'type': 'categorical',
                'values': str_values,
                'label': f'normal_{k}',
                'source': 'normalPostTest',
            }

    # experiencePostTest
    exp_avail = sum(1 for a in alunos if a.get('experiencePostTest'))
    if exp_avail:
        ept_keys = set()
        for a in alunos:
            if a.get('experiencePostTest'):
                ept_keys.update(a['experiencePostTest'].keys())
        for k in sorted(ept_keys):
            values = [a.get('experiencePostTest', {}).get(k, '') for a in alunos]
            str_values = [str(v) if v is not None else '' for v in values]
            fields[f'experiencePostTest.{k}'] = {
                'type': 'categorical',
                'values': str_values,
                'label': f'experience_{k}',
                'source': 'experiencePostTest',
            }

    # appliedFilter
    filter_avail = sum(1 for a in alunos if a.get('appliedFilter'))
    if filter_avail:
        ft_keys = set()
        for a in alunos:
            if a.get('appliedFilter'):
                ft_keys.update(a['appliedFilter'].keys())
        for k in sorted(ft_keys):
            values = [a.get('appliedFilter', {}).get(k, '') for a in alunos]
            vals_clean = [v for v in values if v != '']
            if not vals_clean:
                continue
            is_num = all(isinstance(v, (int, float)) for v in vals_clean)
            if is_num:
                vals_final = [float(a.get('appliedFilter', {}).get(k, 0)) for a in alunos]
                fields[f'appliedFilter.{k}'] = {
                    'type': 'numerical',
                    'values': vals_final,
                    'label': f'filter_{k}',
                    'source': 'appliedFilter',
                }
            else:
                str_vals = [str(a.get('appliedFilter', {}).get(k, '')) for a in alunos]
                fields[f'appliedFilter.{k}'] = {
                    'type': 'categorical',
                    'values': str_vals,
                    'label': f'filter_{k}',
                    'source': 'appliedFilter',
                }

    return fields


# ── GENERATE GRAPH ─────────────────────────────────────────────

def generate_graph(field_key, field_data, alunos, output_dir):
    ftype = field_data['type']
    values = field_data['values']
    label = field_data['label']

    os.makedirs(output_dir, exist_ok=True)
    safe_name = label.replace('/', '_').replace('\\', '_').replace('.', '_')
    png_path = os.path.join(output_dir, f'{safe_name}.png')

    fig, ax = plt.subplots(figsize=(10, 6))

    if ftype == 'numerical':
        vals_num = [v for v in values if v is not None]
        if not vals_num:
            plt.close(fig)
            return None
        ax.hist(vals_num, bins=min(30, len(set(vals_num))), edgecolor='white',
                color='steelblue', alpha=0.7)
        ax.set_xlabel(label)
        ax.set_ylabel('Frequencia')
        ax.set_title(f'Distribuicao de {label}')
        stats_text = (f'n={len(vals_num)}\n'
                      f'Media={np.mean(vals_num):.1f}\n'
                      f'Mediana={np.median(vals_num):.1f}\n'
                      f'DP={np.std(vals_num):.1f}')
        ax.text(0.95, 0.95, stats_text, transform=ax.transAxes,
                fontsize=9, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.7))

    elif ftype in ('categorical', 'binary'):
        counter = Counter(values)
        labels_list = list(counter.keys())
        counts = list(counter.values())
        bars = ax.bar(range(len(labels_list)), counts, color='coral', edgecolor='white')
        ax.set_xticks(range(len(labels_list)))
        ax.set_xticklabels(labels_list, rotation=45, ha='right', fontsize=9)
        ax.set_ylabel('Contagem')
        ax.set_title(f'Distribuicao de {label}')
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(count), ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    fig.savefig(png_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return png_path


def generate_cross_graph(field_x, field_y, alunos, output_dir):
    fx_data = field_x['values']
    fy_data = field_y['values']
    lx = field_x['label']
    ly = field_y['label']
    tx = field_x['type']
    ty = field_y['type']

    os.makedirs(output_dir, exist_ok=True)
    safe_name = f'{lx}_vs_{ly}'.replace('/', '_').replace('\\', '_').replace('.', '_')
    png_path = os.path.join(output_dir, f'{safe_name}.png')

    fig, ax = plt.subplots(figsize=(10, 6))

    if tx == 'numerical' and ty == 'numerical':
        ax.scatter(fx_data, fy_data, alpha=0.6, color='steelblue')
        ax.set_xlabel(lx)
        ax.set_ylabel(ly)
        ax.set_title(f'{lx} vs {ly}')
        if len(fx_data) > 1:
            m, b = np.polyfit(fx_data, fy_data, 1)
            x_line = np.linspace(min(fx_data), max(fx_data), 100)
            ax.plot(x_line, m * x_line + b, color='red', linestyle='--', alpha=0.7)

    elif tx == 'categorical' and ty == 'numerical':
        df_dict = {}
        for cat, val in zip(fx_data, fy_data):
            df_dict.setdefault(cat, []).append(val)
        labels = sorted(df_dict.keys())
        data_groups = [df_dict[k] for k in labels]
        bp = ax.boxplot(data_groups, tick_labels=labels, patch_artist=True)
        for patch in bp['boxes']:
            patch.set_facecolor('lightblue')
        ax.set_xlabel(lx)
        ax.set_ylabel(ly)
        ax.set_title(f'{ly} por {lx}')
        ax.tick_params(axis='x', rotation=45)

    elif tx == 'numerical' and ty == 'categorical':
        df_dict = {}
        for cat, val in zip(fy_data, fx_data):
            df_dict.setdefault(cat, []).append(val)
        labels = sorted(df_dict.keys())
        data_groups = [df_dict[k] for k in labels]
        bp = ax.boxplot(data_groups, tick_labels=labels, patch_artist=True)
        for patch in bp['boxes']:
            patch.set_facecolor('lightgreen')
        ax.set_xlabel(ly)
        ax.set_ylabel(lx)
        ax.set_title(f'{lx} por {ly}')
        ax.tick_params(axis='x', rotation=45)

    else:
        pairs = list(zip(fx_data, fy_data))
        cats_x = sorted(set(fx_data))
        cats_y = sorted(set(fy_data))
        counts = defaultdict(lambda: defaultdict(int))
        for cx, cy in pairs:
            counts[cx][cy] += 1
        x = np.arange(len(cats_x))
        w = 0.8 / len(cats_y)
        for i, cy in enumerate(cats_y):
            heights = [counts[cx].get(cy, 0) for cx in cats_x]
            ax.bar(x + i * w, heights, w, label=cy)
        ax.set_xticks(x + w * (len(cats_y) - 1) / 2)
        ax.set_xticklabels(cats_x, rotation=45, ha='right')
        ax.legend(title=ly)
        ax.set_xlabel(lx)
        ax.set_ylabel('Contagem')
        ax.set_title(f'{lx} vs {ly}')

    plt.tight_layout()
    fig.savefig(png_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return png_path


# ── GENERATE REPORT ────────────────────────────────────────────

def generate_report(fields, selected_keys, graphs, alunos, cross_key=None):
    lines = []
    L = lambda s: lines.append(s)

    L('# NAVINCLUD - Relatorio Estatistico')
    L(f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}')
    L(f'Total de alunos: {len(alunos)}')
    L('')

    for key in selected_keys:
        fd = fields[key]
        L(f'## {fd["label"]}')
        L('')
        L(f'- **Tipo:** {fd["type"]}')
        L(f'- **Fonte:** {fd["source"]}')
        L('')

        ftype = fd['type']
        values = fd['values']

        if ftype == 'numerical':
            vals_num = [v for v in values if v is not None]
            if vals_num:
                L(f'- **n:** {len(vals_num)}')
                L(f'- **Media:** {np.mean(vals_num):.2f}')
                L(f'- **Mediana:** {np.median(vals_num):.2f}')
                L(f'- **Min:** {min(vals_num):.2f}')
                L(f'- **Max:** {max(vals_num):.2f}')
                L(f'- **Desvio Padrao:** {np.std(vals_num):.2f}')
                L('')
                qs = np.percentile(vals_num, [25, 50, 75])
                L(f'- **Q1 (25%):** {qs[0]:.2f}')
                L(f'- **Q2 (50%):** {qs[1]:.2f}')
                L(f'- **Q3 (75%):** {qs[2]:.2f}')
                L('')

        elif ftype in ('categorical', 'binary'):
            counter = Counter(values)
            total = sum(counter.values())
            L(f'- **n:** {total}')
            L('')
            L('| Valor | Contagem | Percentual |')
            L('|-------|----------|------------|')
            for val, count in counter.most_common():
                pct = count / total * 100 if total else 0
                L(f'| {val} | {count} | {pct:.1f}% |')
            L('')

        if key in graphs and graphs[key]:
            L(f'![Grafico {fd["label"]}]({graphs[key]})')
            L('')

    if cross_key and cross_key in graphs:
        L('## Analise Cruzada')
        L('')
        L(f'![Grafico cruzado]({graphs[cross_key]})')
        L('')

    return '\n'.join(lines)


# ── INTERACTIVE SELECTION ──────────────────────────────────────

def interactive_select(fields):
    sorted_keys = sorted(fields.keys(), key=lambda k: (fields[k]['source'], k))
    safe_print('\nCampos disponiveis:\n')
    for i, key in enumerate(sorted_keys, 1):
        fd = fields[key]
        safe_print(f'  {i:3d}. [{fd["type"]:>10}] {fd["label"]:30s} (fonte: {fd["source"]})')

    safe_print('')
    inp = input('Digite os numeros dos campos (separados por virgula): ').strip()
    indices = []
    for part in inp.split(','):
        part = part.strip()
        if part:
            try:
                idx = int(part)
                if 1 <= idx <= len(sorted_keys):
                    indices.append(idx - 1)
            except ValueError:
                pass

    selected = [sorted_keys[i] for i in indices]
    if not selected:
        safe_print('Nenhum campo valido selecionado. Usando todos.')
        selected = sorted_keys
    return selected


def select_cross_fields(fields):
    sorted_keys = sorted(fields.keys(), key=lambda k: (fields[k]['source'], k))
    safe_print('\nSelecione o PRIMEIRO campo (eixo X):')
    for i, key in enumerate(sorted_keys, 1):
        fd = fields[key]
        safe_print(f'  {i:3d}. [{fd["type"]:>10}] {fd["label"]}')
    safe_print('')
    try:
        ix = int(input('Numero do campo X: ').strip())
    except ValueError:
        return None
    if not (1 <= ix <= len(sorted_keys)):
        return None
    key_x = sorted_keys[ix - 1]

    safe_print(f'\nSelecione o SEGUNDO campo (eixo Y):')
    for i, key in enumerate(sorted_keys, 1):
        fd = fields[key]
        flag = ' <<<' if key == key_x else ''
        safe_print(f'  {i:3d}. [{fd["type"]:>10}] {fd["label"]}{flag}')
    safe_print('')
    try:
        iy = int(input('Numero do campo Y: ').strip())
    except ValueError:
        return None
    if not (1 <= iy <= len(sorted_keys)):
        return None
    key_y = sorted_keys[iy - 1]

    if key_x == key_y:
        safe_print('Os campos devem ser diferentes.')
        return None
    return (key_x, key_y)


# ── PLATE TIMING ANALYSIS ──────────────────────────────────────

PLATE_LABELS = [
    'Control-1', 'Control-2',
    'Deuteranopia-1', 'Deuteranopia-2',
    'Deuteranomaly-1', 'Deuteranomaly-2',
    'Protanopia-1', 'Protanopia-2',
    'Protanomaly-1', 'Protanomaly-2',
    'Tritanopia-1', 'Tritanopia-2',
    'Tritanomaly-1', 'Tritanomaly-2',
    'Achromatopsia-1', 'Achromatopsia-2',
    'Achromatomaly-1', 'Achromatomaly-2',
]


def generate_plate_timing_graphs(alunos, output_dir):
    """Gera 2 graficos de analise de tempo por placa."""
    os.makedirs(output_dir, exist_ok=True)

    has_timings = any('plateTimingsMs' in a.get('testResults', {}) for a in alunos)
    if not has_timings:
        safe_print('  AVISO: JSON nao contem plateTimingsMs. Execute inject_plate_timings.py primeiro.')
        return {}

    g1_path = os.path.join(output_dir, 'tempo_por_placa_normal_vs_deficiente.png')
    g2_path = os.path.join(output_dir, 'top_placas_lentas.png')

    # Separar normais vs deficientes
    normais = [a for a in alunos if a['testResults'].get('correctPercent', 0) >= 90]
    deficientes = [a for a in alunos if a['testResults'].get('correctPercent', 0) < 90]

    # Matrizes de tempos: alunos x 18 placas
    def extract_timings(group):
        return np.array([a['testResults']['plateTimingsMs'] for a in group])

    t_normais = extract_timings(normais) if normais else np.zeros((0, 18))
    t_deficientes = extract_timings(deficientes) if deficientes else np.zeros((0, 18))

    fig, ax = plt.subplots(figsize=(14, 6))
    x = np.arange(18)
    w = 0.35

    if len(t_normais) > 0:
        media_normais = np.mean(t_normais, axis=0)
        std_normais = np.std(t_normais, axis=0)
        ax.bar(x - w/2, media_normais, w, yerr=std_normais,
               label=f'Normais (n={len(normais)})', color='steelblue', alpha=0.8, capsize=3)

    if len(t_deficientes) > 0:
        media_def = np.mean(t_deficientes, axis=0)
        std_def = np.std(t_deficientes, axis=0)
        ax.bar(x + w/2, media_def, w, yerr=std_def,
               label=f'Deficientes (n={len(deficientes)})', color='coral', alpha=0.8, capsize=3)

    ax.set_xticks(x)
    ax.set_xticklabels(PLATE_LABELS, rotation=45, ha='right', fontsize=8)
    ax.set_ylabel('Tempo de Reacao Medio (ms)')
    ax.set_title('Tempo de Reacao por Placa: Normais vs. Deficientes')
    ax.legend()
    plt.tight_layout()
    fig.savefig(g1_path, dpi=150, bbox_inches='tight')
    plt.close(fig)

    # Grafico 2: Top placas mais lentas (apenas deficientes)
    fig, ax = plt.subplots(figsize=(12, 8))
    if len(t_deficientes) > 0:
        media_def = np.mean(t_deficientes, axis=0)
        # Ranking: placas onde deficientes mais desviam da propria media
        diff_from_own = media_def - np.mean(t_normais, axis=0) if len(t_normais) > 0 else media_def
        top_indices = np.argsort(diff_from_own)[::-1][:6]  # top 6

        colors = ['#e74c3c' if i < 3 else '#f39c12' for i in range(6)]
        ax.barh(range(6), diff_from_own[top_indices][::-1], color=colors[::-1], edgecolor='white')
        ax.set_yticks(range(6))
        ax.set_yticklabels([PLATE_LABELS[i] for i in top_indices[::-1]])
        ax.set_xlabel('Diferenca de Tempo vs. Normais (ms)')
        ax.set_title('Top 6 Placas com Maior Diferenca de Tempo (Deficientes - Normais)')
        for i, v in enumerate(diff_from_own[top_indices][::-1]):
            ax.text(v + 10, i, f'{v:.0f}ms', va='center', fontsize=9)
    else:
        ax.text(0.5, 0.5, 'Sem dados de deficientes', ha='center', va='center', transform=ax.transAxes)

    plt.tight_layout()
    fig.savefig(g2_path, dpi=150, bbox_inches='tight')
    plt.close(fig)

    graphs = {}
    if os.path.isfile(g1_path):
        graphs['tempo_por_placa'] = g1_path
    if os.path.isfile(g2_path):
        graphs['top_placas_lentas'] = g2_path
    return graphs


# ── MAIN ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='NAVINCLUD - Estatisticas e Graficos')
    parser.add_argument('--json', default='export/navinclud_agregado.json',
                        help='Caminho do JSON agregado (default: export/navinclud_agregado.json)')
    parser.add_argument('--output', default='stats_output',
                        help='Diretorio de saida (default: stats_output)')
    parser.add_argument('--auto', action='store_true',
                        help='Modo automatico (sem interacao)')
    parser.add_argument('--fields', default='',
                        help='Campos para analise separados por virgula (modo --auto)')
    parser.add_argument('--cross', action='store_true',
                        help='Modo cruzado (seleciona 2 campos)')
    parser.add_argument('--type', choices=['univariate', 'bivariate', 'ambos'], default='ambos',
                        help='Tipo de analise (default: ambos)')
    parser.add_argument('--com-tempos', action='store_true',
                        help='Inclui analise de tempo por placa (requer JSON com plateTimingsMs)')
    args = parser.parse_args()

    if args.com_tempos:
        enriched_alternatives = [
            args.json.replace('.json', '_com_tempos.json'),
            os.path.join(os.path.dirname(args.json) or '.', 'navinclud_com_tempos.json'),
        ]
        enriched_path = None
        for p in enriched_alternatives:
            if os.path.isfile(p):
                enriched_path = p
                break
        if enriched_path:
            args.json = enriched_path
        else:
            safe_print(f'AVISO: JSON enriquecido nao encontrado (busquei: {", ".join(enriched_alternatives)})')
            safe_print('Execute: python inject_plate_timings.py')
            safe_print('Continuando com JSON normal...')

    if not os.path.isfile(args.json):
        safe_print(f'Erro: Arquivo JSON nao encontrado: {args.json}')
        safe_print('Execute primeiro aggregate_results.py')
        sys.exit(1)

    alunos = load_alunos(args.json)
    fields = extract_fields(alunos)
    output_dir = args.output

    if not fields:
        safe_print('Nenhum campo extraido do JSON.')
        sys.exit(1)

    # Mode selection
    if args.auto:
        if args.fields:
            selected_keys = [k for k in fields if fields[k]['label'].replace('error_', '').replace('score_', '').replace('perception_', '').replace('filter_', '') in args.fields.split(',') or fields[k]['label'] in args.fields.split(',')]
            if not selected_keys:
                # fallback: match by field name containing any of the requested
                selected_keys = [k for k in fields if any(f.strip().lower() in k.lower() for f in args.fields.split(','))]
            if not selected_keys:
                safe_print(f'Nenhum campo correspondeu a: {args.fields}')
                selected_keys = list(fields.keys())[:5]
        else:
            selected_keys = list(fields.keys())[:5]
        do_cross = args.cross
    else:
        safe_print(f'\nNAVINCLUD - Analise Estatistica')
        safe_print(f'JSON: {args.json}')
        safe_print(f'Alunos: {len(alunos)}')
        safe_print(f'Campos extraidos: {len(fields)}')
        safe_print('')

        if args.cross:
            pair = select_cross_fields(fields)
            if pair is None:
                safe_print('Selecao cancelada.')
                return
            selected_keys = list(pair)
            do_cross = True
        else:
            selected_keys = interactive_select(fields)
            do_cross = False

    os.makedirs(output_dir, exist_ok=True)
    graphs = {}
    reported_keys = []
    cross_key = None

    if not do_cross:
        safe_print(f'\nGerando graficos para {len(selected_keys)} campo(s)...')
        for key in selected_keys:
            safe_print(f'  {fields[key]["label"]}... ', end='')
            png = generate_graph(key, fields[key], alunos, output_dir)
            if png:
                graphs[key] = png
                safe_print('OK')
            else:
                safe_print('pulado')
        reported_keys = selected_keys
    else:
        key_x, key_y = selected_keys
        safe_print(f'\nGerando grafico cruzado: {fields[key_x]["label"]} vs {fields[key_y]["label"]}... ')
        png = generate_cross_graph(fields[key_x], fields[key_y], alunos, output_dir)
        if png:
            cross_key = f'{key_x}_vs_{key_y}'
            graphs[cross_key] = png
            safe_print('OK')
        else:
            safe_print('ERRO')
        reported_keys = selected_keys

    plate_graphs = {}
    if args.com_tempos:
        safe_print('\nGerando analise de tempo por placa...')
        plate_graphs = generate_plate_timing_graphs(alunos, output_dir)
        for name, path in plate_graphs.items():
            safe_print(f'  {name}.png OK')

    report = generate_report(fields, reported_keys, graphs, alunos, cross_key)

    # Append plate timing section if available
    if plate_graphs:
        report += '\n---\n'
        report += '# Analise de Tempo de Reacao por Placa\n\n'
        report += 'Dados simulados a partir do avgReactionTimeMs real de cada aluno.\n\n'
        if 'tempo_por_placa' in plate_graphs:
            report += f'![Tempo por Placa: Normais vs Deficientes]({plate_graphs["tempo_por_placa"]})\n\n'
        if 'top_placas_lentas' in plate_graphs:
            report += f'![Top Placas Mais Lentas]({plate_graphs["top_placas_lentas"]})\n\n'
        report += '## Interpretacao\n\n'
        report += '- **Deficientes** tendem a ter tempos mais altos nas placas correspondentes ao seu tipo de defeito.\n'
        report += '- **Normais** mantem tempos relativamente constantes em todas as 18 placas.\n'
        report += '- A diferenca de tempo entre normais e deficientes nas placas criticas pode indicar o grau de dificuldade imposto pelo daltonismo.\n'
        report += '- Nota: os timings individuais foram simulados com base na media real de cada aluno e na distribuicao de erros por tipo. Variacao intra-teste foi modelada com ruido gaussiano de ~15%.\n\n'

    md_path = os.path.join(output_dir, 'relatorio_estatistico.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(report)
    safe_print(f'\nRelatorio salvo: {md_path}')

    # Also show in console
    safe_print('')
    safe_print(report[:2000])
    if len(report) > 2000:
        safe_print('... (relatorio truncado no console)')

    total_graphs = len(graphs) + len(plate_graphs)
    safe_print(f'\nArquivos gerados em: {os.path.abspath(output_dir)}')
    safe_print('  - relatorio_estatistico.md')
    safe_print(f'  - {total_graphs} grafico(s) .png ({len(graphs)} campos + {len(plate_graphs)} tempo)')


if __name__ == '__main__':
    main()
