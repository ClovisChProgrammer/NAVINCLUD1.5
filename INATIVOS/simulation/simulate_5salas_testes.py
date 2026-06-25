#!/usr/bin/env python3
"""
NAVINCLUD - Simulador de Testes para 5 Salas (100 alunos)
Usa Chrome for Testing e chromedriver.

Uso: python simulation/simulate_5salas_testes.py [opcoes]
  --fast          reacoes rapidas (0.5-2s) para testar fluxo
  --resume        NAO deleta perfil existente (continua de onde parou)
  --skip N        pula os primeiros N alunos (ex: --skip 73)
  --seed N        seed fixa para reprodutibilidade (padrao: 42)
  (padrao)        reacoes realistas (2-11s) para simulacao final
"""

import argparse
import json
import os
import random
import sys
import time
import zipfile
import io
import urllib.request
import shutil

import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (NoSuchElementException, TimeoutException,
                                        NoSuchWindowException, WebDriverException)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.join(_SCRIPT_DIR, "..")

CHROMEDRIVER_PATH = os.path.join(_PROJECT_ROOT, "chromedriver-win64", "chromedriver.exe")
EXTENSION_PATH = _PROJECT_ROOT
CFT_DIR = os.path.join(_PROJECT_ROOT, "chrome_for_testing")
CFT_EXE = os.path.join(CFT_DIR, "chrome-win64", "chrome.exe")
TEMP_PROFILE_DIR = os.path.join(_PROJECT_ROOT, "perfil_temporario")
PROGRESS_FILE = os.path.join(_PROJECT_ROOT, "simulacao_progresso.json")
EXT_ID_FILE = os.path.join(_PROJECT_ROOT, "extension_id.txt")

parser = argparse.ArgumentParser(description="Simulador NAVINCLUD")
parser.add_argument("--fast", action="store_true", help="Reacoes rapidas (0.5-2s)")
parser.add_argument("--resume", action="store_true", help="Nao deleta perfil existente")
parser.add_argument("--skip", type=int, default=0, help="Pula N alunos iniciais")
parser.add_argument("--seed", type=int, default=42, help="Seed para reprodutibilidade")
args = parser.parse_args()

FAST_MODE = args.fast
RESUME_MODE = args.resume
SKIP_STUDENTS = args.skip
RANDOM_SEED = args.seed

if SKIP_STUDENTS > 0:
    RESUME_MODE = True

PLATES = [
    {"id": 1,  "correct": "12", "type": "control"},
    {"id": 2,  "correct": "73", "type": "control"},
    {"id": 3,  "correct": "29", "type": "protanopia"},
    {"id": 4,  "correct": "45", "type": "protanopia"},
    {"id": 5,  "correct": "6",  "type": "protanomaly"},
    {"id": 6,  "correct": "8",  "type": "protanomaly"},
    {"id": 7,  "correct": "8",  "type": "deuteranopia"},
    {"id": 8,  "correct": "5",  "type": "deuteranopia"},
    {"id": 9,  "correct": "2",  "type": "deuteranomaly"},
    {"id": 10, "correct": "15", "type": "deuteranomaly"},
    {"id": 11, "correct": "6",  "type": "tritanopia"},
    {"id": 12, "correct": "3",  "type": "tritanopia"},
    {"id": 13, "correct": "26", "type": "tritanomaly"},
    {"id": 14, "correct": "42", "type": "tritanomaly"},
    {"id": 15, "correct": "7",  "type": "achromatopsia"},
    {"id": 16, "correct": "16", "type": "achromatopsia"},
    {"id": 17, "correct": "4",  "type": "achromatomaly"},
    {"id": 18, "correct": "10", "type": "achromatomaly"},
]

DEFECT_PLATE_INDICES = {
    "protan":   [2, 3, 4, 5],
    "deuteran": [6, 7, 8, 9],
    "tritan":   [10, 11, 12, 13],
}

CLASSES_ORDER = ["3A", "3B", "2A", "2B", "1A"]

CLASSES = {
    "3A": {"total": 19, "males": 16, "age_range": (16, 19), "age_mode": 18,
           "defects": [("deuteran", "M"), ("deuteran", "M")]},
    "3B": {"total": 17, "males": 13, "age_range": (17, 22), "age_mode": 18,
           "defects": [("deuteran", "M"), ("tritan", "M")]},
    "2A": {"total": 22, "males": 16, "age_range": (16, 19), "age_mode": 17,
           "defects": []},
    "2B": {"total": 24, "males": 16, "age_range": (16, 20), "age_mode": 17,
           "defects": [("deuteran", "M"), ("protan", "M")]},
    "1A": {"total": 18, "males": 11, "age_range": (15, 19), "age_mode": 16,
           "defects": [("protan", "F")]},
}

PERCEPTION_SETS = [
    ["Facil", "Interessante"],
    ["Facil", "Divertido"],
    ["Dificil", "Informativo"],
    ["Interessante", "Informativo"],
    ["Divertido", "Estressante"],
    ["Facil"],
    ["Dificil"],
    ["Interessante", "Divertido"],
    ["Interessante", "Estressante", "Informativo"],
    ["Facil", "Informativo"],
    ["Interessante"],
    ["Informativo"],
]

NAVIGATION_EASE_OPTIONS = ["Muito Facil", "Facil", "Neutra"]


def weighted_age(age_range, mode):
    lo, hi = age_range
    ages = list(range(lo, hi + 1))
    weights = []
    for a in ages:
        if a == mode:
            weights.append(40)
        elif abs(a - mode) == 1:
            weights.append(25)
        else:
            weights.append(10)
    return random.choices(ages, weights=weights, k=1)[0]


def generate_students(config, class_name):
    total = config["total"]
    males = config["males"]
    females = total - males
    sexes = ["M"] * males + ["F"] * females
    random.shuffle(sexes)

    defect_indices = set()
    for defect_type, sex in config["defects"]:
        for i, s in enumerate(sexes):
            if s == sex and i not in defect_indices:
                defect_indices.add(i)
                break

    defect_map = {}
    for idx, (defect_type, sex) in zip(defect_indices, config["defects"]):
        defect_map[idx] = defect_type

    students = []
    for i in range(total):
        age = weighted_age(config["age_range"], config["age_mode"])
        is_defective = i in defect_indices
        defect_type = defect_map.get(i)
        students.append({
            "sexo": "Masculino" if sexes[i] == "M" else "Feminino",
            "idade": age,
            "turma": class_name,
            "is_defective": is_defective,
            "defect_type": defect_type,
        })
    return students


def pick_perception():
    return random.choice(PERCEPTION_SETS)


def ensure_chrome_for_testing():
    if os.path.exists(CFT_EXE):
        print(f"  Chrome for Testing ja baixado em: {CFT_DIR}")
        return CFT_EXE

    print(f"  Chrome for Testing nao encontrado. Baixando (150MB)...")
    print(f"  (isso ocorre apenas uma vez)")

    os.makedirs(CFT_DIR, exist_ok=True)

    chrome_version = "148.0.7778.178"
    url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/win64/chrome-win64.zip"
    zip_path = os.path.join(CFT_DIR, "chrome-win64.zip")

    print(f"  URL: {url}")
    try:
        resp = requests.get(url, stream=True, timeout=300)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = int(downloaded / total * 100)
                    if pct % 25 == 0 and downloaded < total:
                        print(f"    Download: {pct}%")
        print(f"    Download: 100%")
    except Exception as e:
        print(f"  ERRO ao baixar Chrome for Testing: {e}")
        return None

    print("  Extraindo...")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(CFT_DIR)
        os.remove(zip_path)
    except Exception as e:
        print(f"  ERRO ao extrair: {e}")
        return None

    if os.path.exists(CFT_EXE):
        print(f"  Chrome for Testing pronto: {CFT_EXE}")
        return CFT_EXE
    else:
        print(f"  ERRO: chrome.exe nao encontrado apos extracao.")
        return None


def kill_chrome_processes():
    try:
        import subprocess
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"],
                       capture_output=True, text=True, timeout=10)
        time.sleep(2)
    except Exception:
        pass


def setup_driver(cft_exe, resume=False):
    print("  Fechando processos do Chrome existentes...")
    kill_chrome_processes()

    if not resume and os.path.exists(TEMP_PROFILE_DIR):
        shutil.rmtree(TEMP_PROFILE_DIR, ignore_errors=True)
    elif resume and os.path.exists(TEMP_PROFILE_DIR):
        print(f"  MODO RETOMADA: Preservando perfil existente em {TEMP_PROFILE_DIR}")

    print("  Iniciando Chrome for Testing com extensao NAVINCLUD...")
    options = Options()
    options.binary_location = cft_exe
    options.add_argument(f"--load-extension={EXTENSION_PATH}")
    options.add_argument(f"--user-data-dir={TEMP_PROFILE_DIR}")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-search-engine-choice-screen")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-features=ChromeWhatsNewUI")

    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(15)
    return driver


def get_extension_id(driver):
    cached = None
    if os.path.exists(EXT_ID_FILE):
        with open(EXT_ID_FILE, "r") as f:
            cached = f.read().strip()
        if cached:
            print(f"  Usando ID salvo: {cached}")
            return cached

    print("  Detectando ID da extensao NAVINCLUD...")
    try:
        driver.get("chrome://extensions/")
        ext_id = driver.execute_script("""
            function check() {
                const mgr = document.querySelector('extensions-manager');
                if (!mgr) return null;
                const root = mgr.shadowRoot;
                const itemsList = root.querySelector('#itemsList');
                if (!itemsList) return null;
                const iroot = itemsList.shadowRoot;
                const item = iroot.querySelector('extensions-item');
                return item ? item.id : null;
            }
            let result = check();
            if (result) return result;
            return new Promise((resolve) => {
                let start = Date.now();
                function poll() {
                    result = check();
                    if (result) { resolve(result); return; }
                    if (Date.now() - start > 10000) { resolve(null); return; }
                    setTimeout(poll, 200);
                }
                poll();
            });
        """)
        if ext_id:
            print(f"  Extensao encontrada: {ext_id}")
            with open(EXT_ID_FILE, "w") as f:
                f.write(ext_id)
            return ext_id
    except Exception as e:
        print(f"  Aviso: deteccao falhou ({e})")

    val = input("  Digite manualmente o ID (chrome://extensions/ > NAVINCLUD > ID): ").strip()
    if val:
        with open(EXT_ID_FILE, "w") as f:
            f.write(val)
    return val if val else None


def run_single_test(driver, ext_id, student, main_handle):
    wizard_url = f"chrome-extension://{ext_id}/wizard.html"
    wait = WebDriverWait(driver, 15)

    # Abre wizard em JANELA separada (nao aba) para que
    # chrome.windows.remove() nao mate a janela principal.
    support_handle = driver.current_window_handle
    driver.switch_to.new_window('window')
    wiz_handle = driver.current_window_handle
    driver.get(wizard_url)

    try:
        wait.until(EC.presence_of_element_located((By.ID, "preSexo")))
    except TimeoutException:
        print("ERRO: Pre-teste nao carregou.")
        return False

    sexo_select = Select(driver.find_element(By.ID, "preSexo"))
    sexo_select.select_by_visible_text(student["sexo"])
    idade_el = driver.find_element(By.ID, "preIdade")
    idade_el.clear()
    idade_el.send_keys(str(student["idade"]))
    turma_el = driver.find_element(By.ID, "preTurma")
    turma_el.clear()
    turma_el.send_keys(student["turma"])
    driver.find_element(By.ID, "pre-test-btn").click()

    try:
        wait.until(EC.presence_of_element_located((By.ID, "quiz-container")))
    except TimeoutException:
        print("ERRO: Quiz nao iniciou.")
        return False

    defect_plates = set()
    if student["is_defective"]:
        defect_plates = set(DEFECT_PLATE_INDICES.get(student["defect_type"], []))

    for i, plate in enumerate(PLATES):
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".option-btn")))
        except TimeoutException:
            print(f"ERRO: Opcoes da placa {i+1} nao apareceram.")
            return False

        is_defect = i in defect_plates
        if FAST_MODE:
            reaction = random.uniform(0.5, 2)
        elif student["is_defective"]:
            reaction = random.uniform(6, 11)
        else:
            if random.random() < 0.4:
                reaction = random.uniform(6, 11)
            else:
                reaction = random.uniform(2, 5)
        time.sleep(round(reaction, 1))

        correct_answer = plate["correct"]
        options = driver.find_elements(By.CSS_SELECTOR, ".option-btn")

        clicked = False
        if is_defect:
            for opt in options:
                if opt.text != correct_answer:
                    opt.click()
                    clicked = True
                    break
            if not clicked:
                options[0].click()
        else:
            for opt in options:
                if opt.text == correct_answer:
                    opt.click()
                    clicked = True
                    break
            if not clicked:
                options[0].click()

    try:
        wait.until(EC.presence_of_element_located((By.NAME, "testPerception")))
    except TimeoutException:
        print("ERRO: Tela de percepcao nao apareceu.")
        return False

    perception_choices = pick_perception()
    for choice in perception_choices:
        try:
            cb = driver.find_element(By.XPATH,
                f"//input[@name='testPerception' and @value='{choice}']")
            if not cb.is_selected():
                cb.click()
        except NoSuchElementException:
            pass

    try:
        driver.find_element(By.ID, "perception-btn").click()
    except NoSuchElementException:
        print("ERRO: Botao de percepcao nao encontrado.")
        return False

    if student["is_defective"]:
        try:
            wait.until(EC.presence_of_element_located((By.ID, "start-experience-btn")))
        except TimeoutException:
            print("ERRO: Tela de convite para experiencia nao apareceu.")
            return False

        driver.find_element(By.ID, "start-experience-btn").click()
        time.sleep(5)

        wiz_dead = False
        try:
            driver.current_url
        except Exception:
            wiz_dead = True

        if wiz_dead:
            # Janela do wizard foi fechada; volta pra support_handle
            try:
                driver.switch_to.window(support_handle)
            except Exception:
                pass

        # Procura handle com experience.html entre as janelas abertas
        exp_found = False
        deadline = time.time() + 10
        while time.time() < deadline:
            for h in driver.window_handles:
                try:
                    driver.switch_to.window(h)
                    if "experience.html" in driver.current_url:
                        exp_found = True
                        break
                except Exception:
                    continue
            if exp_found:
                break
            time.sleep(1)

        if not exp_found:
            # Navega uma janela existente para experience.html
            for h in driver.window_handles:
                try:
                    driver.switch_to.window(h)
                    driver.get(f"chrome-extension://{ext_id}/experience.html")
                    exp_found = True
                    break
                except Exception:
                    continue

        if not exp_found:
            print("ERRO: Nao foi possivel acessar experience.html.")
            return False

        try:
            wait.until(EC.element_to_be_clickable((By.ID, "exit-experience-btn")))
        except TimeoutException:
            pass

        time.sleep(random.uniform(2, 5))

        try:
            driver.find_element(By.ID, "exit-experience-btn").click()
        except Exception:
            try:
                driver.execute_script("document.getElementById('exit-experience-btn').click()")
            except Exception:
                pass

        try:
            wait.until(EC.presence_of_element_located((By.NAME, "visualImprovement")))
        except TimeoutException:
            print("ERRO: Questionario pos-experiencia nao apareceu.")
            return False

        driver.find_element(By.XPATH,
            "//input[@name='visualImprovement' and @value='Sim']").click()
        nav_ease = random.choice(NAVIGATION_EASE_OPTIONS)
        driver.find_element(By.XPATH,
            f"//input[@name='navigationEase' and @value='{nav_ease}']").click()
        driver.find_element(By.XPATH,
            "//input[@name='wouldRecommend' and @value='Sim']").click()
        driver.find_element(By.XPATH,
            "//input[@name='comfortLevel' and @value='Sim']").click()
        driver.find_element(By.ID, "save-responses-btn").click()

        try:
            wait.until(EC.presence_of_element_located((By.ID, "thankyou-screen")))
        except TimeoutException:
            pass

        # Sai da pagina experience.html para cancelar pending
        # setTimeout do showThankYou (que faria chrome.windows.remove
        # e mataria a sessao do Selenium)
        try:
            driver.get("about:blank")
        except Exception:
            pass

        # Fecha handles excedentes, deixa 1 about:blank
        for h in list(driver.window_handles)[1:]:
            try:
                driver.switch_to.window(h)
                driver.close()
            except Exception:
                pass
        if driver.window_handles:
            try:
                driver.switch_to.window(driver.window_handles[0])
                if "about:blank" not in driver.current_url:
                    driver.get("about:blank")
            except Exception:
                pass
        return True

    else:
        try:
            wait.until(EC.presence_of_element_located((By.NAME, "alreadyTaken")))
        except TimeoutException:
            print("ERRO: Pos-teste normal nao apareceu.")
            return False

        already_taken = "Sim" if random.random() < 0.08 else "Nao"
        driver.find_element(By.XPATH,
            f"//input[@name='alreadyTaken' and @value='{already_taken}']").click()
        driver.find_element(By.ID, "normal-post-btn").click()

        try:
            wait.until(EC.presence_of_element_located((By.ID, "new-test-btn")))
        except TimeoutException:
            print("ERRO: Tela de parabeis nao apareceu.")
            return False

        driver.find_element(By.ID, "new-test-btn").click()

        # Fecha janela do wizard e abas excedentes
        try:
            driver.switch_to.window(wiz_handle)
            driver.close()
        except Exception:
            pass
        for h in list(driver.window_handles)[1:]:
            try:
                driver.switch_to.window(h)
                driver.close()
            except Exception:
                pass
        if driver.window_handles:
            try:
                driver.switch_to.window(driver.window_handles[0])
                driver.get("about:blank")
            except Exception:
                pass
        return True


def save_progress(completed_classes, students_completed=0):
    data = {
        "completed_classes": completed_classes,
        "students_completed": students_completed,
        "timestamp": time.time()
    }
    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def load_progress():
    try:
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"completed_classes": [], "students_completed": 0, "timestamp": 0}


def main():
    global SKIP_STUDENTS
    random.seed(RANDOM_SEED)

    print("=" * 55)
    print("  NAVINCLUD - SIMULADOR DE TESTES PARA 5 SALAS")
    print("  Total: 100 alunos | Salas: 3A 3B 2A 2B 1A")
    print(f"  Seed: {RANDOM_SEED} (reprodutivel)")
    if FAST_MODE:
        print("  MODO RAPIDO (reacoes de 0.5-2s) - Apenas para teste de fluxo")
    if RESUME_MODE:
        print("  MODO RETOMADA (preserva perfil existente)")
    if SKIP_STUDENTS > 0:
        print(f"  PULANDO primeiros {SKIP_STUDENTS} alunos")
    print("=" * 55)

    progress = load_progress()
    completed = set(progress.get("completed_classes", []))
    students_completed_from_file = progress.get("students_completed", 0)

    if SKIP_STUDENTS == 0 and students_completed_from_file > 0:
        SKIP_STUDENTS = students_completed_from_file
        print(f"\n  Progresso encontrado: {students_completed_from_file} alunos completados")
        print(f"  Usando --skip {SKIP_STUDENTS} automaticamente\n")

    all_students = []
    for class_name in CLASSES_ORDER:
        config = CLASSES[class_name]
        estudantes = generate_students(config, class_name)
        all_students.extend(estudantes)

    cft_exe = ensure_chrome_for_testing()
    if not cft_exe:
        print("\nERRO: Chrome for Testing nao disponivel.")
        print("Baixe manualmente de https://googlechromelabs.github.io/chrome-for-testing/")
        print("e extraia em:", CFT_DIR)
        sys.exit(1)

    driver = setup_driver(cft_exe, resume=RESUME_MODE)
    try:
        ext_id = get_extension_id(driver)
        if not ext_id:
            print("\nERRO: Nao foi possivel determinar o ID da extensao.")
            print("Abra chrome://extensions/, ative Modo Desenvolvedor,")
            print("veja o ID da extensao NAVINCLUD e execute novamente.")
            driver.quit()
            sys.exit(1)

        driver.get("about:blank")
        main_handle = driver.current_window_handle
        print(f"  Janela ancora: {main_handle}\n")

        current_class = None
        class_completed_students = 0

        for global_idx, student in enumerate(all_students, 1):
            if global_idx <= SKIP_STUDENTS:
                if current_class != student["turma"]:
                    current_class = student["turma"]
                    class_completed_students = 0
                class_completed_students += 1
                continue

            if current_class != student["turma"]:
                if current_class is not None and current_class in completed:
                    pass
                current_class = student["turma"]
                if current_class in completed:
                    print(f"  Sala {current_class} ja completada (pulando).")
                    continue

                config = CLASSES[current_class]
                num_defect = sum(1 for s in all_students if s["turma"] == current_class and s["is_defective"])

                print(f"{'='*50}")
                print(f"  SALA {current_class}: {config['total']} alunos "
                      f"({config['males']}M/{config['total']-config['males']}F)"
                      f"  |  {num_defect} com diagnostico")
                print(f"{'='*50}")
                class_completed_students = 0

            config = CLASSES[current_class]
            class_students = [s for s in all_students if s["turma"] == current_class]
            class_idx = class_completed_students + 1

            turma_display = student["turma"]
            sexo_display = "M" if student["sexo"] == "Masculino" else "F"
            idade_display = student["idade"]
            defect_str = f" [{student['defect_type']}]" if student["is_defective"] else ""
            print(f"    [{class_idx:2d}/{config['total']}] (global {global_idx}/100) "
                  f"{turma_display} | {sexo_display} | {idade_display:2d}a"
                  f"{defect_str} ... ", end="", flush=True)

            try:
                ok = run_single_test(driver, ext_id, student, main_handle)
                if not ok:
                    print("FALHA")
                    save_progress(list(completed), global_idx - 1)
                    sys.exit(1)
                print("OK")
                class_completed_students += 1
                save_progress(list(completed), global_idx)
            except KeyboardInterrupt:
                print("\n\n  Interrompido pelo usuario.")
                save_progress(list(completed), global_idx - 1)
                driver.quit()
                sys.exit(0)
            except Exception as e:
                print(f"ERRO: {e}")
                save_progress(list(completed), global_idx - 1)
                driver.quit()
                sys.exit(1)

            if class_completed_students >= config["total"]:
                completed.add(current_class)
                save_progress(list(completed), global_idx)

                if current_class != CLASSES_ORDER[-1]:
                    print()
                    try:
                        input("  >>> SALA CONCLUIDA! Faca o EXPORT manual no popup "
                              "e pressione Enter para continuar...")
                    except (EOFError, KeyboardInterrupt):
                        print()
                    driver.switch_to.window(main_handle)
                    print()

        print(f"\n{'='*55}")
        print("  TODAS AS 5 SALAS CONCLUIDAS COM SUCESSO!")
        print("  100 alunos simulados | 7 diagnosticados")
        print(f"{'='*55}")
        print(f"\n  Dados salvos no chrome.storage.local da extensao.")
        print(f"  Use o botao EXPORTAR no popup NAVINCLUD para extrair.")

    except KeyboardInterrupt:
        print("\n\n  Interrompido pelo usuario.")
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        if os.path.exists(PROGRESS_FILE):
            try:
                os.remove(PROGRESS_FILE)
            except Exception:
                pass


if __name__ == "__main__":
    main()
