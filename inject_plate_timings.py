#!/usr/bin/env python3
"""
NAVINCLUD - Simulacao de Tempo de Reacao por Placa
Le o JSON agregado, gera timings individuais para cada placa (1-18)
baseados no avgReactionTimeMs real + erros por tipo de defeito.

Uso:
  python inject_plate_timings.py
  python inject_plate_timings.py --input export/navinclud_agregado.json
  python inject_plate_timings.py --output export/navinclud_com_tempos.json
"""

import os, sys, json, argparse
import numpy as np


TOTAL_PLATES = 18

# Mapeamento placa -> tipo de defeito (2 placas por tipo)
# Confirmado com usuario que segue esta ordem
PLATE_DEFECT_MAP = [
    (0, 'control'), (1, 'control'),
    (2, 'deuteranopia'), (3, 'deuteranopia'),
    (4, 'deuteranomaly'), (5, 'deuteranomaly'),
    (6, 'protanopia'), (7, 'protanopia'),
    (8, 'protanomaly'), (9, 'protanomaly'),
    (10, 'tritanopia'), (11, 'tritanopia'),
    (12, 'tritanomaly'), (13, 'tritanomaly'),
    (14, 'achromatopsia'), (15, 'achromatopsia'),
    (16, 'achromatomaly'), (17, 'achromatomaly'),
]

"""
Regras de geracao para cada aluno:
- Normais (correctPercent >= 90):
    * Todas as 18 placas: tempo variando uniformemente ~15% ao redor da media
    * Nenhum erro
- Deficientes (correctPercent < 90):
    * Placas sem erro: mesma logica dos normais
    * Placas com erro: penalidade de +50% a +80% sobre a media
    * Erros distribuiDOS conforme errorsByType (ex: deuteranopia=2 significa
      que 2 placas do tipo deuteranopia tiveram erro)
"""


def seed_from_reaction(avg):
    """Gera seed deterministica a partir da media para reproducibilidade."""
    return int(avg * 1000) % (2**31)


def simulate_student_timings(aluno):
    tr = aluno.get('testResults', {})
    avg = tr.get('avgReactionTimeMs', 3000)
    correct_pct = tr.get('correctPercent', 100)
    errors_bt = tr.get('errorsByType', {})

    if not avg:
        avg = 3000

    rng = np.random.default_rng(seed_from_reaction(avg))
    is_deficient = correct_pct < 90

    timings = [0.0] * TOTAL_PLATES
    errors = [False] * TOTAL_PLATES

    # Constroi fila de erros por tipo
    # Ex: errors_bt['deuteranopia'] = 2 significa que as 2 placas
    # de deuteranopia estao erradas.
    # Nota: o maximo de erros por tipo e 2 (so ha 2 placas por tipo).
    defect_error_map = {}
    for defect_type, error_count in errors_bt.items():
        if error_count > 0 and is_deficient:
            # Quantas placas desse tipo estao erradas (max 2)
            n_errors = min(int(error_count), 2)
            defect_error_map[defect_type] = n_errors

    # Gera timings placa por placa
    for plate_idx, defect_type in PLATE_DEFECT_MAP:
        # Sorteia desvio percentual: -15% a +15% em torno da media
        deviation = rng.uniform(-0.15, 0.15)
        base_time = avg * (1 + deviation)

        # Verifica se esta placa especifica esta errada
        if is_deficient and defect_type in defect_error_map:
            remaining = defect_error_map[defect_type]
            if remaining > 0:
                # Penalidade de +50% a +80%
                penalty = rng.uniform(0.50, 0.80)
                base_time *= (1 + penalty)
                errors[plate_idx] = True
                defect_error_map[defect_type] = remaining - 1

        timings[plate_idx] = round(base_time, 1)

    # Ajuste fino: recalcula media para aproximar da media real
    current_avg = np.mean(timings)
    if current_avg > 0:
        scale = avg / current_avg
        timings = [round(t * scale, 1) for t in timings]

    return timings, errors


def inject_all(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        alunos = json.load(f)

    total = len(alunos)
    pos_count = 0

    for aluno in alunos:
        timings, errors = simulate_student_timings(aluno)
        aluno['testResults']['plateTimingsMs'] = timings
        aluno['testResults']['plateErrors'] = errors
        if aluno.get('testResults', {}).get('correctPercent', 100) < 90:
            pos_count += 1

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(alunos, f, indent=2, ensure_ascii=False)

    print(f'OK: {total} alunos processados ({pos_count} positivos)')
    print(f'Saida: {output_path}')
    tamanho_kb = os.path.getsize(output_path) / 1024
    print(f'Tamanho: {tamanho_kb:.0f} KB')

    return alunos


def validate_timings(alunos):
    """Verifica se as medias simuladas estao proximas das reais."""
    diffs = []
    for aluno in alunos:
        tr = aluno.get('testResults', {})
        real_avg = tr.get('avgReactionTimeMs', 0)
        simulated = tr.get('plateTimingsMs', [])
        if simulated and real_avg:
            sim_avg = np.mean(simulated)
            diffs.append(abs(sim_avg - real_avg))
    if diffs:
        print(f'Erro medio absoluto: {np.mean(diffs):.1f}ms')
        print(f'Erro maximo: {max(diffs):.1f}ms')


def main():
    parser = argparse.ArgumentParser(description='NAVINCLUD - Simulacao de Tempo por Placa')
    parser.add_argument('--input', default='export/navinclud_agregado.json',
                        help='JSON agregado de entrada')
    parser.add_argument('--output', default='export/navinclud_com_tempos.json',
                        help='JSON de saida com tempos simulados')
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f'Erro: JSON nao encontrado: {args.input}')
        print('Execute primeiro aggregate_results.py')
        sys.exit(1)

    alunos = inject_all(args.input, args.output)
    validate_timings(alunos)


if __name__ == '__main__':
    main()
