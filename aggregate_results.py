#!/usr/bin/env python3
"""
NAVINCLUD - Agregação de Resultados de Testes
Lê todos os arquivos JSON de testes de múltiplas máquinas (via pen-drive)
e gera um relatório consolidado.
"""

import os
import json
import argparse
from collections import defaultdict


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


def load_all_results(directory):
    """Carrega todos os arquivos JSON de resultados do diretório."""
    all_tests = []
    terminal_count = defaultdict(int)
    
    for filename in os.listdir(directory):
        if not filename.startswith('navinclud_'):
            continue
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                
                required_keys = ['testId', 'timestamp', 'testResults', 'preTest']
                if isinstance(data, list):
                    valid = [TypoCorrector.correct_nested(item) for item in data 
                            if isinstance(item, dict) and all(k in item for k in required_keys)]
                    all_tests.extend(valid)
                    for t in valid:
                        tid = t.get('terminalId', 'unknown')
                        terminal_count[tid] += 1
                elif isinstance(data, dict) and all(k in data for k in required_keys):
                    corrected = TypoCorrector.correct_nested(data)
                    all_tests.append(corrected)
                    tid = corrected.get('terminalId', 'unknown')
                    terminal_count[tid] += 1
                else:
                    print(f"Ignorado {filename}: schema inválido (chaves ausentes)")
        except json.JSONDecodeError as e:
            print(f"Erro JSON em {filename}: {e}")
        except Exception as e:
            print(f"Erro ao ler {filename}: {e}")
    
    return all_tests, terminal_count

def generate_report(all_tests, terminal_count):
    """Gera relatório consolidado."""
    total_testers = len(all_tests)
    
    # Contagem por sexo
    sex_counts = defaultdict(int)
    for test in all_tests:
        sexo = test.get('preTest', {}).get('sexo', 'Não informado')
        sex_counts[sexo] += 1
    
    # Contagem por turma
    turma_counts = defaultdict(int)
    for test in all_tests:
        turma = test.get('preTest', {}).get('turma', 'Não informado')
        turma_counts[turma] += 1
    
    # Contagem por idade
    idade_counts = defaultdict(int)
    for test in all_tests:
        idade = test.get('preTest', {}).get('idade', 'Não informado')
        idade_counts[idade] += 1
    
    # Testes sem deficiência (>=90% corretas)
    normal_tests = [t for t in all_tests if t.get('testResults', {}).get('correctPercent', 0) >= 90]
    # Testes com deficiência (<90% corretas)
    deficient_tests = [t for t in all_tests if t.get('testResults', {}).get('correctPercent', 0) < 90]
    
    # Contagem por tipo de deficiência
    defect_counts = defaultdict(lambda: defaultdict(int))
    for test in deficient_tests:
        defect = test.get('testResults', {}).get('detectedDefect', 'unknown')
        sexo = test.get('preTest', {}).get('sexo', 'Não informado')
        if defect != 'none':
            defect_counts[defect][sexo] += 1
    
    # Contagem por terminal (máquina)
    total_terminals = len(terminal_count)
    
    # Montar relatório
    report = []
    report.append("=" * 60)
    report.append("RELATÓRIO NAVINCLUD - RESULTADOS CONSOLIDADOS")
    report.append("=" * 60)
    report.append("")
    
    report.append(f"Total de testadores: {total_testers}")
    report.append(f"Total de terminais/máquinas: {total_terminals}")
    report.append("")
    
    report.append("-" * 40)
    report.append("1. DISTRIBUIÇÃO POR SEXO (Todos os Testes)")
    report.append("-" * 40)
    for sexo, count in sex_counts.items():
        pct = (count / total_testers * 100) if total_testers > 0 else 0
        report.append(f"  {sexo}: {count} ({pct:.1f}%)")
    report.append("")
    
    report.append("-" * 40)
    report.append("1a. DISTRIBUIÇÃO POR TURMA")
    report.append("-" * 40)
    for turma in sorted(turma_counts.keys()):
        count = turma_counts[turma]
        pct = (count / total_testers * 100) if total_testers > 0 else 0
        report.append(f"  {turma}: {count} ({pct:.1f}%)")
    report.append("")
    
    report.append("-" * 40)
    report.append("1b. DISTRIBUIÇÃO POR IDADE")
    report.append("-" * 40)
    for idade in sorted(idade_counts.keys(), key=lambda x: int(x) if str(x).isdigit() else 999):
        count = idade_counts[idade]
        pct = (count / total_testers * 100) if total_testers > 0 else 0
        report.append(f"  {idade} anos: {count} ({pct:.1f}%)")
    report.append("")
    
    report.append("-" * 40)
    report.append("2. TESTADORES SEM DEFICIÊNCIA (>=90% acertos)")
    report.append("-" * 40)
    normal_count = len(normal_tests)
    normal_pct = (normal_count / total_testers * 100) if total_testers > 0 else 0
    report.append(f"  Total: {normal_count} ({normal_pct:.1f}%)")
    normal_sex = defaultdict(int)
    for test in normal_tests:
        sexo = test.get('preTest', {}).get('sexo', 'Não informado')
        normal_sex[sexo] += 1
    for sexo, count in normal_sex.items():
        pct = (count / normal_count * 100) if normal_count > 0 else 0
        report.append(f"    {sexo}: {count} ({pct:.1f}%)")
    report.append("")
    
    report.append("-" * 40)
    report.append(" 3. TESTADORES COM DEFICIÊNCIA (<=89% acertos)")
    report.append("-" * 40)
    deficient_count = len(deficient_tests)
    deficient_pct = (deficient_count / total_testers * 100) if total_testers > 0 else 0
    report.append(f"  Total: {deficient_count} ({deficient_pct:.1f}%)")
    report.append("")
    
    report.append("  Por tipo de deficiência e sexo:")
    for defect, sex_data in defect_counts.items():
        report.append(f"    {defect.upper()}:")
        total_defect = sum(sex_data.values())
        for sexo, count in sex_data.items():
            pct = (count / total_defect * 100) if total_defect > 0 else 0
            report.append(f"      {sexo}: {count} ({pct:.1f}%)")
    report.append("")
    
    report.append("-" * 40)
    report.append("4. TESTES POR TERMINAL/MÁQUINA")
    report.append("-" * 40)
    for tid, count in terminal_count.items():
        report.append(f"  {tid}: {count} testes")
    report.append("")
    
    report.append("-" * 40)
    report.append("5. RESPOSTAS DE QUESTIONÁRIOS FINAIS")
    report.append("-" * 40)
    
    # Normal post-test
    normal_post = [t for t in all_tests if 'normalPostTest' in t]
    if normal_post:
        report.append("  Testes Normais (>=90%):")
        already_taken = defaultdict(int)
        perceptions = defaultdict(int)
        for test in normal_post:
            at = test.get('normalPostTest', {}).get('alreadyTaken', 'N/A')
            already_taken[at] += 1
            for p in test.get('testResults', {}).get('testPerception', []):
                perceptions[p] += 1

        report.append("    Ja fizera o teste antes:")
        for k, v in already_taken.items():
            report.append(f"      {k}: {v}")
        report.append("    Percepcao do teste:")
        for k, v in perceptions.items():
            report.append(f"      {k}: {v}")
    else:
        report.append("  Testes Normais (>=90%): Nenhum")

    # Deficient post-test
    deficient_post = [t for t in all_tests if 'experiencePostTest' in t and t.get('experiencePostTest', {}).get('visualImprovement', '') != '']
    if deficient_post:
        report.append("")
        report.append("  Testes Deficientes (<=89%):")
        visual = defaultdict(int)
        nav_ease = defaultdict(int)
        recommend = defaultdict(int)
        comfort = defaultdict(int)
        for test in deficient_post:
            post = test.get('experiencePostTest', {})
            visual[post.get('visualImprovement', 'N/A')] += 1
            nav_ease[post.get('navigationEase', 'N/A')] += 1
            recommend[post.get('wouldRecommend', 'N/A')] += 1
            comfort[post.get('comfortLevel', 'N/A')] += 1

        report.append("    Melhora na visualizacao das cores:")
        for k, v in visual.items():
            report.append(f"      {k}: {v}")
        report.append("    Facilidade de navegacao:")
        for k, v in nav_ease.items():
            report.append(f"      {k}: {v}")
        report.append("    Indicaria a extensao:")
        for k, v in recommend.items():
            report.append(f"      {k}: {v}")
        report.append("    Cores mais confortaveis:")
        for k, v in comfort.items():
            report.append(f"      {k}: {v}")
    else:
        report.append("")
        report.append("  Testes Deficientes (<=89%): Nenhum")
    
    report.append("")
    report.append("=" * 60)
    report.append("FIM DO RELATÓRIO")
    report.append("=" * 60)
    
    return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Agregar resultados do NAVINCLUD')
    parser.add_argument('directory', help='Diretório contendo os arquivos JSON de testes')
    parser.add_argument('-o', '--output', help='Arquivo de saída para o relatório (opcional)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Erro: Diretório '{args.directory}' não encontrado.")
        return
    
    print(f"Lendo resultados de: {args.directory}")
    all_tests, terminal_count = load_all_results(args.directory)
    
    if not all_tests:
        print("Nenhum resultado encontrado.")
        return
    
    print(f"Total de {len(all_tests)} testes carregados de {len(terminal_count)} terminais.")
    
    report = generate_report(all_tests, terminal_count)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8-sig') as f:
            f.write(report)
        print(f"Relatório salvo em: {args.output}")
    else:
        print("\n" + report)

if __name__ == '__main__':
    main()
