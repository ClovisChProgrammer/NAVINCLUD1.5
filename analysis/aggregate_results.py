#!/usr/bin/env python3
"""
NAVINCLUD - Agregação de Resultados de Testes
Lê todos os arquivos JSON de uma pasta, padroniza turmas,
e exporta dados estruturados (JSON + CSV) para análise estatística.

Uso:
  python analysis/aggregate_results.py <diretorio>
  python analysis/aggregate_results.py <diretorio> --export <pasta_saida>
  python analysis/aggregate_results.py <diretorio> -o relatorio.txt
"""

import os, json, csv, argparse, re, sys, uuid
from collections import defaultdict
from datetime import datetime


# ──────────────────────────────────────────────────────────────
# CORREÇÃO DE DIGITAÇÃO (typos encontrados nos dados reais)
# ──────────────────────────────────────────────────────────────

class TypoCorrector:
    TYPO_MAP = {
        'deutanopia': 'deuteranopia',
        'deutanomaly': 'deuteranomaly',
        'achromaopia': 'achromatopsia',
    }

    @classmethod
    def correct(cls, value):
        if isinstance(value, str):
            return cls.TYPO_MAP.get(value, value)
        return value

    @classmethod
    def correct_nested(cls, obj):
        if isinstance(obj, dict):
            return {k: cls.correct_nested(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [cls.correct_nested(item) for item in obj]
        elif isinstance(obj, str):
            return cls.TYPO_MAP.get(obj, obj)
        return obj


# ──────────────────────────────────────────────────────────────
# PADRONIZAÇÃO DE TURMA
# ──────────────────────────────────────────────────────────────

def normalize_turma(raw):
    """Padroniza turma para o formato 'XDS Y' (ex: 3DS A, 2DS B).
    
    Regras:
      - '3A', '3a', '3 A', '3DS A'  → '3DS A'
      - '2B', '2b', '2 B', '2DS B'  → '2DS B'
      - qualquer outro valor        → 'OUTROS'
    """
    if not raw or not isinstance(raw, str):
        return 'OUTROS'
    raw = raw.strip().upper()
    # Already normalized: XDS Y
    m = re.match(r'^([1-3])DS\s*([AB])$', raw)
    if m:
        return f'{m.group(1)}DS {m.group(2)}'
    # Short format: XY (ex: 3A, 2B)
    m = re.match(r'^([1-3])\s*([AB])$', raw)
    if m:
        return f'{m.group(1)}DS {m.group(2)}'
    return 'OUTROS'


# ──────────────────────────────────────────────────────────────
# EXTRAÇÃO DE TESTES DO JSON
# ──────────────────────────────────────────────────────────────

REQUIRED_KEYS = ['testId', 'timestamp', 'testResults', 'preTest']

def extract_tests_from_data(data):
    """Extrai testes de dados que podem ser lista [] ou dict {id: {...}}."""
    valid = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and all(k in item for k in REQUIRED_KEYS):
                valid.append(TypoCorrector.correct_nested(item))
    elif isinstance(data, dict):
        if all(k in data for k in REQUIRED_KEYS):
            valid.append(TypoCorrector.correct_nested(data))
        else:
            for key, value in data.items():
                if isinstance(value, dict) and all(k in value for k in REQUIRED_KEYS):
                    valid.append(TypoCorrector.correct_nested(value))
    return valid


# ──────────────────────────────────────────────────────────────
# CARREGAMENTO
# ──────────────────────────────────────────────────────────────

def load_all_results(directory):
    """Carrega todos os arquivos JSON do diretório (sem filtro de prefixo)."""
    all_tests_dict = {}
    file_stats = []
    files_found = 0
    files_loaded = 0

    for filename in sorted(os.listdir(directory)):
        if not filename.endswith('.json'):
            continue
        files_found += 1
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            valid = extract_tests_from_data(data)
            if valid:
                novos = 0
                for t in valid:
                    tid = t.get('testId')
                    if tid and tid not in all_tests_dict:
                        all_tests_dict[tid] = t
                        novos += 1
                file_stats.append((filename, len(valid), novos))
                files_loaded += 1
            else:
                file_stats.append((filename, 0, 0))
        except (json.JSONDecodeError, Exception) as e:
            file_stats.append((filename, -1, 0, str(e)))

    all_tests = list(all_tests_dict.values())
    return all_tests, file_stats, files_found


def detect_defect_info(tests):
    """Retorna contagem e metadados sobre defeitos."""
    total = len(tests)
    normais = [t for t in tests if t.get('testResults', {}).get('correctPercent', 0) >= 90]
    deficientes = [t for t in tests if t.get('testResults', {}).get('correctPercent', 0) < 90]
    defect_counts = defaultdict(lambda: defaultdict(int))
    for t in deficientes:
        defect = t.get('testResults', {}).get('detectedDefect', 'unknown')
        sexo = t.get('preTest', {}).get('sexo', 'Nao informado')
        if defect != 'none':
            defect_counts[defect][sexo] += 1
    return normais, deficientes, defect_counts


# ──────────────────────────────────────────────────────────────
# EXPORTAÇÃO JSON
# ──────────────────────────────────────────────────────────────

def export_json(tests, filepath):
    """Exporta lista limpa de testes como JSON."""
    # Aplica padronização de turma e achata campos para consumo
    export = []
    for t in tests:
        entry = dict(t)
        turma_raw = entry.get('preTest', {}).get('turma', '')
        entry['preTest']['turma_normalized'] = normalize_turma(turma_raw)
        entry['preTest']['turma_original'] = turma_raw
        export.append(entry)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(export, f, ensure_ascii=False, indent=2)
    return len(export)


# ──────────────────────────────────────────────────────────────
# EXPORTAÇÃO CSV
# ──────────────────────────────────────────────────────────────

def _flatten_test(t):
    """Achata um teste em dicionário plano para CSV."""
    row = OrderedDict()
    pre = t.get('preTest', {})
    res = t.get('testResults', {})
    err = res.get('errorsByType', {})
    score = res.get('scorePointsByType', {})
    normal_post = t.get('normalPostTest', {})
    exp_post = t.get('experiencePostTest', {})
    filt = t.get('appliedFilter', {})
    perc = res.get('testPerception', [])

    # Identificação
    row['testId'] = t.get('testId', '')
    row['timestamp'] = t.get('timestamp', '')
    row['terminalId'] = t.get('terminalId', '')

    # Pré-teste
    row['sexo'] = pre.get('sexo', '')
    row['idade'] = pre.get('idade', '')
    row['turma_original'] = pre.get('turma', '')
    row['turma'] = normalize_turma(pre.get('turma', ''))

    # Resultados
    row['correctCount'] = res.get('correctCount', '')
    row['correctPercent'] = res.get('correctPercent', '')
    row['avgReactionTimeMs'] = res.get('avgReactionTimeMs', '')
    row['detectedDefect'] = res.get('detectedDefect', 'none')
    row['controlPlateErrors'] = res.get('controlPlateErrors', False)
    row['totalPlates'] = res.get('totalPlates', 18)

    # Percepção (multi-select → colunas 0/1)
    for opt in ['Facil', 'Dificil', 'Interessante', 'Divertido', 'Estressante', 'Informativo']:
        row[f'percepcao_{opt}'] = '1' if opt in perc else '0'

    # Erros por tipo
    for tipo in ['control', 'protanopia', 'protanomaly', 'deuteranopia',
                 'deuteranomaly', 'tritanopia', 'tritanomaly',
                 'achromatopsia', 'achromatomaly']:
        row[f'erro_{tipo}'] = err.get(tipo, 0)

    # Score por tipo
    for tipo in ['control', 'protanopia', 'protanomaly', 'deuteranopia',
                 'deuteranomaly', 'tritanopia', 'tritanomaly',
                 'achromatopsia', 'achromatomaly']:
        row[f'score_{tipo}'] = score.get(tipo, 0)

    # Pós-teste normal (visão normal)
    row['alreadyTaken'] = normal_post.get('alreadyTaken', '')

    # Pós-experiência (deficientes)
    row['visualImprovement'] = exp_post.get('visualImprovement', '')
    row['navigationEase'] = exp_post.get('navigationEase', '')
    row['wouldRecommend'] = exp_post.get('wouldRecommend', '')
    row['comfortLevel'] = exp_post.get('comfortLevel', '')

    # Filtro aplicado
    row['filterType'] = filt.get('type', '')
    row['filterIntensity'] = filt.get('intensity', '')
    row['filterShift'] = filt.get('shift', '')

    return row


def export_csv(tests, filepath):
    """Exporta CSV plano (1 linha por aluno)."""
    if not tests:
        return 0
    rows = [_flatten_test(t) for t in tests]
    fieldnames = list(rows[0].keys())
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def export_by_sala(tests, basepath):
    """Exporta JSON + CSV agrupados por sala e totais."""
    grouped = defaultdict(list)
    for t in tests:
        turma = normalize_turma(t.get('preTest', {}).get('turma', ''))
        grouped[turma].append(t)

    # Exporta individual por sala
    sala_stats = []
    for sala in sorted(grouped.keys()):
        sala_tests = grouped[sala]
        # CSV da sala
        sala_csv = os.path.join(basepath, f'sala_{sala.replace(" ", "_")}.csv')
        export_csv(sala_tests, sala_csv)
        # JSON da sala
        sala_json = os.path.join(basepath, f'sala_{sala.replace(" ", "_")}.json')
        export_json(sala_tests, sala_json)
        # Contagem de positivos
        _, deficientes, defect_counts = detect_defect_info(sala_tests)
        total_positivos = sum(sum(sexo.values()) for sexo in defect_counts.values())
        # Tipos de defeito
        tipos = list(defect_counts.keys())
        sala_stats.append({
            'sala': sala,
            'alunos': len(sala_tests),
            'positivos': total_positivos,
            'tipos_defeito': tipos
        })

    # JSON agregado por sala
    with open(os.path.join(basepath, 'navinclud_por_sala.json'), 'w', encoding='utf-8') as f:
        json.dump({
            'total_salas': len(grouped),
            'total_alunos': len(tests),
            'salas': sala_stats,
            'dados_por_sala': {s: [{'testId': t['testId'],
                                    'sexo': t.get('preTest', {}).get('sexo', ''),
                                    'idade': t.get('preTest', {}).get('idade', ''),
                                    'correctPercent': t.get('testResults', {}).get('correctPercent', 0),
                                    'detectedDefect': t.get('testResults', {}).get('detectedDefect', 'none')}
                                   for t in grouped[s]] for s in sorted(grouped.keys())}
        }, f, ensure_ascii=False, indent=2)

    # CSV resumo por sala
    sala_csv_path = os.path.join(basepath, 'navinclud_por_sala.csv')
    with open(sala_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Sala', 'Alunos', 'Positivos', 'Tipos de Defeito'])
        for s in sala_stats:
            writer.writerow([s['sala'], s['alunos'], s['positivos'],
                            ', '.join(s['tipos_defeito']) if s['tipos_defeito'] else 'Nenhum'])

    return grouped, sala_stats


# ──────────────────────────────────────────────────────────────
# RELATÓRIO TEXTUAL
# ──────────────────────────────────────────────────────────────

def generate_report(tests, file_stats, files_found):
    """Gera relatório textual completo."""
    total = len(tests)
    normais, deficientes, defect_counts = detect_defect_info(tests)

    # Agrupa por sala
    sala_counts = defaultdict(lambda: {'total': 0, 'positivos': 0})
    for t in tests:
        turma = normalize_turma(t.get('preTest', {}).get('turma', ''))
        sala_counts[turma]['total'] += 1
        if t.get('testResults', {}).get('correctPercent', 0) < 90:
            sala_counts[turma]['positivos'] += 1

    # Sexo
    sex_counts = defaultdict(int)
    for t in tests:
        s = t.get('preTest', {}).get('sexo', 'Nao informado')
        sex_counts[s] += 1

    # Percepção
    perception_counts = defaultdict(int)
    for t in tests:
        for p in t.get('testResults', {}).get('testPerception', []):
            perception_counts[p] += 1

    HR = '-' * 65
    HR2 = '=' * 65

    lines = []
    L = lambda s: lines.append(s)

    L(HR2)
    L('  NAVINCLUD - RELATORIO DE AGREGACAO DE RESULTADOS')
    L(f'  Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}')
    L(HR2)
    L('')

    # Arquivos processados
    L(HR)
    L('  ARQUIVOS PROCESSADOS')
    L(HR)
    L(f'  Total de arquivos JSON encontrados: {files_found}')
    for fname, total_tests, novos in file_stats:
        if total_tests == -1:
            L(f'  ! ERRO: {fname}')
        elif total_tests == 0:
            L(f'  — {fname}: 0 testes validos')
        else:
            L(f'  ✓ {fname}: {novos} novos testes')
    L('')

    # Resumo geral
    L(HR)
    L('  RESUMO GERAL')
    L(HR)
    L(f'  Total de alunos testados:  {total}')
    L(f'  Visao normal (>=90%):      {len(normais)} ({(len(normais)/total*100):.1f}%)' if total else '')
    L(f'  Com deficiencia (<90%):    {len(deficientes)} ({(len(deficientes)/total*100):.1f}%)' if total else '')
    L('')

    # Tabela por sala
    L(HR)
    L('  DISTRIBUICAO POR SALA')
    L(HR)
    L(f'  {"Sala":<12} {"Alunos":>8} {"Positivos":>10} {"%":>6}')
    sep = '-' * 36
    L(f'  {sep}')
    salas_ordenadas = sorted(sala_counts.keys(),
                             key=lambda x: (0 if x != 'OUTROS' else 1, x))
    for sala in salas_ordenadas:
        sc = sala_counts[sala]
        pct = (sc['positivos'] / sc['total'] * 100) if sc['total'] else 0
        L(f'  {sala:<12} {sc["total"]:>8} {sc["positivos"]:>10} {pct:>5.1f}%')
    L(f'  {sep}')
    L(f'  {"TOTAL":<12} {total:>8} {len(deficientes):>10} {(len(deficientes)/total*100):>5.1f}%' if total else '')
    L('')

    # Distribuição por sexo
    L(HR)
    L('  DISTRIBUICAO POR SEXO')
    L(HR)
    for sexo in ['Masculino', 'Feminino', 'Outro', 'Prefiro nao responder', 'Nao informado']:
        c = sex_counts.get(sexo, 0)
        if c > 0:
            L(f'  {sexo:<30} {c:>4} ({(c/total*100):.1f}%)' if total else '')
    L('')

    # Distribuição por idade
    L(HR)
    L('  DISTRIBUICAO POR IDADE')
    L(HR)
    idades = defaultdict(int)
    for t in tests:
        i = t.get('preTest', {}).get('idade', 'N/A')
        idades[str(i)] += 1
    for idade in sorted(idades.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        L(f'  {idade:>2} anos: {idades[idade]:>4} aluno(s)')
    L('')

    # Defeitos detectados
    L(HR)
    L('  DEFEITOS DETECTADOS (POSITIVOS)')
    L(HR)
    if defect_counts:
        for defect, sex_data in defect_counts.items():
            total_def = sum(sex_data.values())
            L(f'  {defect.upper()}: {total_def} aluno(s)')
            for sexo, c in sex_data.items():
                L(f'    {sexo}: {c}')
    else:
        L('  Nenhum defeito detectado.')
    L('')

    # Percepção do teste
    L(HR)
    L('  PERCEPCAO DO TESTE (multi-select)')
    L(HR)
    for p in sorted(perception_counts.keys()):
        L(f'  {p:<20} {perception_counts[p]:>4}')

    # Questionários
    L('')
    L(HR)
    L('  QUESTIONARIOS')
    L(HR)

    # AlreadyTaken
    normal_post = [t for t in tests if 'normalPostTest' in t]
    if normal_post:
        at_counts = defaultdict(int)
        for t in normal_post:
            at_counts[t.get('normalPostTest', {}).get('alreadyTaken', 'N/A')] += 1
        L(f'  Alunos normais que responderam: {len(normal_post)}')
        for k, v in at_counts.items():
            L(f'    Ja fez antes? {k}: {v}')

    # Pós-experiência
    exp_post = [t for t in tests if 'experiencePostTest' in t and t.get('experiencePostTest', {}).get('visualImprovement', '') != '']
    if exp_post:
        L('')
        L(f'  Alunos deficientes que responderam: {len(exp_post)}')
        for campo, label in [('visualImprovement', 'Melhora na visualizacao'),
                             ('navigationEase', 'Facilidade de navegacao'),
                             ('wouldRecommend', 'Indicaria extensao'),
                             ('comfortLevel', 'Cores mais confortaveis')]:
            vals = defaultdict(int)
            for t in exp_post:
                vals[t.get('experiencePostTest', {}).get(campo, 'N/A')] += 1
            L(f'    {label}:')
            for k, v in vals.items():
                L(f'      {k}: {v}')

    L('')
    L(HR2)
    L('  RESUMO FINAL')
    L(HR2)
    L(f'  Total de salas distintas:        {len(sala_counts)}')
    L(f'  Total de alunos testados:        {total}')
    L(f'  Total de POSITIVOS encontrados:  {len(deficientes)}')
    if defect_counts:
        tipos_list = [f'{d.upper()} ({sum(s.values())})' for d, s in defect_counts.items()]
        L(f'  Tipos de deficiencia:            {", ".join(tipos_list)}')
    L('')
    L(HR2)
    L('  FIM DO RELATORIO')
    L(HR2)

    return '\n'.join(lines)


# ──────────────────────────────────────────────────────────────
# ADICIONAR DADOS MANUAIS (RAPHAEL)
# ──────────────────────────────────────────────────────────────

def create_raphael_entry(directory):
    """Cria arquivo JSON com dados do Raphael (deuteranopia, 2DS A)."""
    entry = {
        "appliedFilter": {
            "enabled": True,
            "intensity": 100,
            "shift": 0.5,
            "type": "deuteranopia"
        },
        "experiencePostTest": {
            "comfortLevel": "Sim",
            "navigationEase": "Muito Facil",
            "visualImprovement": "Sim",
            "wouldRecommend": "Sim"
        },
        "preTest": {
            "idade": 21,
            "sexo": "Masculino",
            "turma": "2A"
        },
        "terminalId": "navinclud-raphael-manual",
        "testId": str(uuid.uuid4()),
        "testResults": {
            "avgReactionTimeMs": 3500,
            "controlPlateErrors": False,
            "correctCount": 12,
            "correctPercent": 66.66666666666667,
            "detectedDefect": "deuteranopia",
            "errorsByType": {
                "achromatomaly": 0, "achromatopsia": 0, "control": 0,
                "deuteranomaly": 3, "deuteranopia": 3,
                "protanomaly": 0, "protanopia": 0,
                "tritanomaly": 0, "tritanopia": 0
            },
            "scorePointsByType": {
                "achromatomaly": 2, "achromatopsia": 2, "control": 2,
                "deuteranomaly": 0, "deuteranopia": 0,
                "protanomaly": 2, "protanopia": 2,
                "tritanomaly": 2, "tritanopia": 2
            },
            "testPerception": ["Interessante", "Informativo"],
            "totalPlates": 18
        },
        "timestamp": "2026-06-10T14:30:00.000Z"
    }
    filepath = os.path.join(directory, 'navinclud_raphael_2DSA.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump([entry], f, ensure_ascii=False, indent=2)
    return filepath


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def safe_print(text):
    """Imprime no console substituindo caracteres problematicos."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('cp1252', errors='replace').decode('cp1252'))


def main():
    parser = argparse.ArgumentParser(
        description='NAVINCLUD - Agregacao de Resultados de Testes')
    parser.add_argument('directory', help='Diretorio com arquivos JSON de testes')
    parser.add_argument('--export', default=None,
                        help='Diretorio para exportar JSON+CSV (opcional)')
    parser.add_argument('-o', '--output', default=None,
                        help='Arquivo de saida para relatorio textual (opcional)')
    parser.add_argument('--raphael', action='store_true', default=True,
                        help='Incluir dados do Raphael (2DS A, deuteranopia)')

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        safe_print(f'Erro: Diretorio "{args.directory}" nao encontrado.')
        sys.exit(1)

    # Incluir dados do Raphael
    if args.raphael:
        try:
            fp = create_raphael_entry(args.directory)
            safe_print(f'OK Dados do Raphael adicionados: {os.path.basename(fp)}')
        except Exception as e:
            safe_print(f'ERRO: Nao foi possivel adicionar Raphael: {e}')

    # Carregar
    safe_print(f'Lendo resultados de: {args.directory}')
    all_tests, file_stats, files_found = load_all_results(args.directory)

    if not all_tests:
        safe_print('Nenhum resultado encontrado.')
        sys.exit(1)

    safe_print(f'Carregados {len(all_tests)} testes de {files_found} arquivo(s).')

    # Relatorio textual
    report = generate_report(all_tests, file_stats, files_found)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        safe_print(f'Relatorio salvo em: {args.output}')
    else:
        safe_print('')
        safe_print(report)

    # Exportacao estruturada
    if args.export:
        export_dir = args.export
        os.makedirs(export_dir, exist_ok=True)

        n_json = export_json(all_tests, os.path.join(export_dir, 'navinclud_agregado.json'))
        safe_print(f'Exportados {n_json} testes para navinclud_agregado.json')

        n_csv = export_csv(all_tests, os.path.join(export_dir, 'navinclud_agregado.csv'))
        safe_print(f'Exportados {n_csv} registros para navinclud_agregado.csv')

        grouped, sala_stats = export_by_sala(all_tests, export_dir)
        safe_print(f'Exportados {len(grouped)} salas individuais')
        sala_list = ', '.join(f'{s} ({st["alunos"]} alunos)' for s, st in zip(sorted(grouped.keys()), sala_stats))
        safe_print(f'  Salas: {sala_list}')
        safe_print(f'Diretorio de exportacao: {export_dir}')


if __name__ == '__main__':
    from collections import OrderedDict
    main()
