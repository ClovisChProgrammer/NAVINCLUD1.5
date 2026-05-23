#!/usr/bin/env python3
"""
Extrai dados do chrome.storage.local da extensao NAVINCLUD.
Copia o perfil para um diretorio temporario limpo.
"""

import json
import os
import sys
import time
import subprocess
import shutil
import tempfile

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


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

CHROMEDRIVER_PATH = os.path.join(os.path.dirname(__file__), "chromedriver-win64", "chromedriver.exe")
CFT_DIR = os.path.join(os.path.dirname(__file__), "chrome_for_testing")
CFT_EXE = os.path.join(CFT_DIR, "chrome-win64", "chrome.exe")
TEMP_PROFILE_DIR = os.path.join(os.path.dirname(__file__), "perfil_temporario")
EXT_ID_FILE = os.path.join(os.path.dirname(__file__), "extension_id.txt")
RESULTADOS_DIR = os.path.join(os.path.dirname(__file__), "resultados")


def kill_chrome_processes():
    try:
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"],
                       capture_output=True, text=True, timeout=10)
        time.sleep(2)
    except Exception:
        pass


def load_extension_id():
    if os.path.exists(EXT_ID_FILE):
        with open(EXT_ID_FILE, "r") as f:
            return f.read().strip()
    return None


def copy_profile_clean(source_dir, dest_dir):
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir, ignore_errors=True)
    
    os.makedirs(dest_dir, exist_ok=True)
    
    exclude_patterns = ['lockfile', 'LOCK', '.lock', 'SingletonLock', 'SingletonCookie', 'SingletonSocket']
    
    for item in os.listdir(source_dir):
        source_item = os.path.join(source_dir, item)
        dest_item = os.path.join(dest_dir, item)
        
        if any(pattern.lower() in item.lower() for pattern in exclude_patterns):
            continue
        
        if os.path.isdir(source_item):
            try:
                shutil.copytree(source_item, dest_item)
            except Exception as e:
                print(f"    Aviso: nao foi possivel copiar {item}: {e}")
        else:
            try:
                shutil.copy2(source_item, dest_item)
            except Exception as e:
                print(f"    Aviso: nao foi possivel copiar {item}: {e}")
    
    return dest_dir


def main():
    print("=" * 60)
    print("  EXTRATOR DE DADOS NAVINCLUD v3")
    print("=" * 60)

    ext_id = load_extension_id()
    if not ext_id:
        print("ERRO: Extension ID nao encontrado.")
        sys.exit(1)
    print(f"  Extension ID: {ext_id}")

    print("\n  Fechando processos Chrome...")
    kill_chrome_processes()

    temp_dir = tempfile.mkdtemp(prefix="navinclud_profile_")
    print(f"\n  Copiando perfil para: {temp_dir}")
    
    try:
        copy_profile_clean(TEMP_PROFILE_DIR, temp_dir)
    except Exception as e:
        print(f"ERRO ao copiar perfil: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        sys.exit(1)

    print("\n  Iniciando Chrome...")
    options = Options()
    options.binary_location = CFT_EXE
    options.add_argument(f"--load-extension={os.path.abspath('.')}")
    options.add_argument(f"--user-data-dir={temp_dir}")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-search-engine-choice-screen")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-features=ChromeWhatsNewUI")

    service = Service(executable_path=CHROMEDRIVER_PATH)
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"ERRO ao iniciar Chrome: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        sys.exit(1)

    try:
        popup_url = f"chrome-extension://{ext_id}/popup.html"
        print(f"  Abrindo: {popup_url}")
        driver.get(popup_url)
        time.sleep(3)

        print("\n  Extraindo dados do chrome.storage.local...")

        all_data = driver.execute_script("""
            return new Promise((resolve) => {
                chrome.storage.local.get(null, function(items) {
                    resolve(JSON.stringify(items));
                });
            });
        """)

        if not all_data or all_data == "{}":
            print("ERRO: Nenhum dado encontrado.")
            driver.quit()
            shutil.rmtree(temp_dir, ignore_errors=True)
            sys.exit(1)

        data = json.loads(all_data)
        print(f"  Chaves encontradas no storage: {len(data)}")

        for k in list(data.keys())[:15]:
            print(f"    - {k}")
        if len(data) > 15:
            print(f"    ... e mais {len(data) - 15}")

        test_history_ids = data.get('testHistoryIds', [])
        print(f"\n  testHistoryIds: {len(test_history_ids)} itens")

        os.makedirs(RESULTADOS_DIR, exist_ok=True)

        testes_por_sala_dict = {}
        testes_por_sala_list = {}
        todos_os_testes_dict = {}
        todos_os_testes_list = []

        for key, value in data.items():
            if key.startswith('test_') and isinstance(value, dict):
                value_corrected = TypoCorrector.correct_nested(value)
                todos_os_testes_dict[key] = value_corrected
                todos_os_testes_list.append(value_corrected)
                pre_test = value_corrected.get('preTest', {})
                if isinstance(pre_test, dict):
                    turma = pre_test.get('turma')
                    if turma:
                        if turma not in testes_por_sala_dict:
                            testes_por_sala_dict[turma] = {}
                            testes_por_sala_list[turma] = []
                        testes_por_sala_dict[turma][key] = value_corrected
                        testes_por_sala_list[turma].append(value_corrected)

        print(f"\n  Testes validos encontrados: {len(todos_os_testes_dict)}")
        print("\n  Distribuicao por sala:")
        for turma in sorted(testes_por_sala_dict.keys()):
            print(f"    Sala {turma}: {len(testes_por_sala_dict[turma])} testes")

        for turma, testes_dict in testes_por_sala_dict.items():
            testes_list = testes_por_sala_list[turma]
            
            filename_dict = os.path.join(RESULTADOS_DIR, f"resultados_{turma}.json")
            with open(filename_dict, "w", encoding="utf-8-sig") as f:
                json.dump(testes_dict, f, indent=2, ensure_ascii=False)
            print(f"\n  [SALVO] {filename_dict} (formato dict)")
            
            filename_list = os.path.join(RESULTADOS_DIR, f"navinclud_{turma}.json")
            with open(filename_list, "w", encoding="utf-8-sig") as f:
                json.dump(testes_list, f, indent=2, ensure_ascii=False)
            print(f"  [SALVO] {filename_list} (formato lista para agregadores)")

        filename_all_dict = os.path.join(RESULTADOS_DIR, "resultados_TODOS_100.json")
        with open(filename_all_dict, "w", encoding="utf-8-sig") as f:
            json.dump(todos_os_testes_dict, f, indent=2, ensure_ascii=False)
        print(f"\n  [SALVO] {filename_all_dict} (formato dict)")

        filename_all_list = os.path.join(RESULTADOS_DIR, "navinclud_TODOS_100.json")
        with open(filename_all_list, "w", encoding="utf-8-sig") as f:
            json.dump(todos_os_testes_list, f, indent=2, ensure_ascii=False)
        print(f"  [SALVO] {filename_all_list} (formato lista para agregadores)")

        filename_dump = os.path.join(RESULTADOS_DIR, "dump_completo_storage.json")
        with open(filename_dump, "w", encoding="utf-8-sig") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  [SALVO] {filename_dump} (dump completo)")

        print("\n" + "=" * 60)
        print("  EXTRACAO CONCLUIDA COM SUCESSO!")
        print("=" * 60)

    finally:
        try:
            driver.quit()
        except Exception:
            pass
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
