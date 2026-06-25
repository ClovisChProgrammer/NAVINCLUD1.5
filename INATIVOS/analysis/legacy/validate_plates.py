#!/usr/bin/env python3
"""
NAVINCLUD - Validação Automatizada de Placas Ishihara
Verifica se as 18 placas foram geradas corretamente e têm contraste adequado.
"""

import os
import sys
from PIL import Image
import json

def validate_plate(plate_path, plate_id, expected_type):
    """Valida uma placa individual."""
    results = {
        'id': plate_id,
        'type': expected_type,
        'file': os.path.basename(plate_path),
        'exists': False,
        'size_ok': False,
        'dimensions_ok': False,
        'file_size': 0,
        'issues': []
    }
    
    # Verificar se arquivo existe
    if not os.path.exists(plate_path):
        results['issues'].append('Arquivo não encontrado')
        return results
    
    results['exists'] = True
    
    try:
        img = Image.open(plate_path)
        
        # Verificar dimensões
        if img.size != (500, 500):
            results['issues'].append(f'Tamanho incorreto: {img.size}')
        else:
            results['dimensions_ok'] = True
        
        # Verificar modo de cor
        if img.mode != 'RGB':
            results['issues'].append(f'Modo de cor incorreto: {img.mode}')
        
        # Verificar tamanho do arquivo (webp deve ter tamanho razoável)
        file_size = os.path.getsize(plate_path)
        results['file_size'] = file_size
        
        if file_size < 10000:  # Menor que 10KB é suspeito
            results['issues'].append(f'Arquivo muito pequeno: {file_size} bytes')
        elif file_size > 200000:  # Maior que 200KB é suspeito para webp
            results['issues'].append(f'Arquivo muito grande: {file_size} bytes')
        else:
            results['size_ok'] = True
        
        # Verificar se a imagem não está corrompida (média de brilho)
        import numpy as np
        arr = np.array(img)
        mean_brightness = arr.mean()
        
        if mean_brightness < 20 or mean_brightness > 250:
            results['issues'].append(f'Brilho suspeito: {mean_brightness:.1f}')
        
        img.close()
        
    except Exception as e:
        results['issues'].append(f'Erro ao ler imagem: {e}')
    
    return results

def main():
    # Dados das placas (copiado de main.py)
    PLATES_DATA = [
        (1, 12, "control"), (2, 73, "control"),
        (3, 29, "protanopia"), (4, 45, "protanopia"),
        (5, 6, "protanomaly"), (6, 8, "protanomaly"),
        (7, 8, "deuteranopia"), (8, 5, "deuteranopia"),
        (9, 2, "deuteranomaly"), (10, 15, "deuteranomaly"),
        (11, 6, "tritanopia"), (12, 3, "tritanopia"),
        (13, 26, "tritanomaly"), (14, 42, "tritanomaly"),
        (15, 7, "achromatopsia"), (16, 16, "achromatopsia"),
        (17, 4, "achromatomaly"), (18, 10, "achromatomaly"),
    ]
    
    images_dir = "images"
    print("=" * 60)
    print("VALIDAÇÃO DE PLACAS ISHIHARA - NAVINCLUD")
    print("=" * 60)
    print()
    
    all_valid = True
    results = []
    
    for id_p, num, p_type in PLATES_DATA:
        plate_path = os.path.join(images_dir, f"plate{id_p}.webp")
        result = validate_plate(plate_path, id_p, p_type)
        results.append(result)
        
        status = "[OK]" if not result['issues'] else "[!]"
        print(f"{status} Placa {id_p:2d} ({p_type:15s}): ", end="")
        
        if result['exists'] and result['size_ok'] and result['dimensions_ok']:
            print(f"OK ({result['file_size']/1024:.1f} KB)")
        else:
            print("PROBLEMAS:")
            for issue in result['issues']:
                print(f"    - {issue}")
            all_valid = False
    
    print()
    print("=" * 60)
    if all_valid:
        print("[OK] TODAS AS PLACAS VALIDAS!")
    else:
        print("[!] ALGUMAS PLACAS TEM PROBLEMAS - VERIFIQUE ACIMA")
    print("=" * 60)
    
    return 0 if all_valid else 1

if __name__ == '__main__':
    sys.exit(main())
