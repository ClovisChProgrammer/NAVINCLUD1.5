#!/usr/bin/env python3
"""
Converte arquivos resultados_*.json (formato dict) para navinclud_*.json (formato lista).
Tambem corrige typos conhecidos.
"""

import json
import os
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


def convert_dict_to_list(dict_data):
    """Converte dict { "test_xxx": {...} } para lista [ {...}, {...} ]."""
    if isinstance(dict_data, list):
        return [TypoCorrector.correct_nested(item) for item in dict_data]
    
    if isinstance(dict_data, dict):
        required = ['testId', 'timestamp', 'testResults', 'preTest']
        
        if all(k in dict_data for k in required):
            return [TypoCorrector.correct_nested(dict_data)]
        
        values_list = []
        for key, value in dict_data.items():
            if isinstance(value, dict) and all(k in value for k in required):
                values_list.append(TypoCorrector.correct_nested(value))
        
        return values_list
    
    return []


def main():
    print("=" * 60)
    print("  CONVERSOR: resultados_*.json -> navinclud_*.json")
    print("=" * 60)

    resultados_dir = os.path.join(os.path.dirname(__file__), "resultados")
    
    if not os.path.isdir(resultados_dir):
        print(f"ERRO: Diretorio nao encontrado: {resultados_dir}")
        return

    arquivos_convertidos = 0
    estatisticas = defaultdict(int)

    for filename in os.listdir(resultados_dir):
        if not filename.startswith('resultados_'):
            continue
        if not filename.endswith('.json'):
            continue
        
        turma = filename.replace('resultados_', '').replace('.json', '')
        novo_nome = f"navinclud_{turma}.json"
        
        caminho_entrada = os.path.join(resultados_dir, filename)
        caminho_saida = os.path.join(resultados_dir, novo_nome)

        print(f"\n  Convertendo: {filename} -> {novo_nome}")

        try:
            with open(caminho_entrada, 'r', encoding='utf-8-sig') as f:
                dados = json.load(f)
            
            lista = convert_dict_to_list(dados)
            
            if not lista:
                print(f"    Aviso: Nenhum teste valido encontrado em {filename}")
                continue

            turma_real = lista[0].get('preTest', {}).get('turma', turma)
            estatisticas[turma_real] = len(lista)
            
            with open(caminho_saida, 'w', encoding='utf-8-sig') as f:
                json.dump(lista, f, indent=2, ensure_ascii=False)
            
            print(f"    OK: {len(lista)} testes da sala {turma_real}")
            arquivos_convertidos += 1

        except json.JSONDecodeError as e:
            print(f"    ERRO: JSON invalido - {e}")
        except Exception as e:
            print(f"    ERRO: {e}")

    print("\n" + "=" * 60)
    print("  RESUMO DA CONVERSAO")
    print("=" * 60)
    print(f"\n  Arquivos convertidos: {arquivos_convertidos}")
    print(f"\n  Distribuicao por turma:")
    
    total = 0
    for turma in sorted(estatisticas.keys()):
        count = estatisticas[turma]
        total += count
        print(f"    {turma}: {count} testes")
    
    print(f"\n  Total: {total} testes")
    print("\n" + "=" * 60)
    print("  CONCLUIDO!")
    print("=" * 60)


if __name__ == "__main__":
    main()
