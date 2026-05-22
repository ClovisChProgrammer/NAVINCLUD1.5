#!/usr/bin/env python3
"""
NAVINCLUD - Simulador de Testes para 5 Salas (100 alunos)
Usa o perfil Chrome real do usuario (extensao ja carregada).
Requer chromedriver na pasta chromedriver-win64/.
"""

import json
import os
import random
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (NoSuchElementException, TimeoutException,
                                        NoSuchWindowException, WebDriverException)

CHROMEDRIVER_PATH = os.path.join(os.path.dirname(__file__), "chromedriver-win64", "chromedriver.exe")
USER_DATA_DIR = r"C:\Users\clovi\AppData\Local\Google\Chrome\User Data"
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "simulacao_progresso.json")
EXT_ID_FILE = os.path.join(os.path.dirname(__file__), "extension_id.txt")

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
    {"id": 10, "correct": "10", "type": "deuteranomaly"},
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


def is_chrome_running():
    try:
        import subprocess
        output = subprocess.run(["tasklist", "/FI", "IMAGENAME eq chrome.exe"],
                                capture_output=True, text=True, timeout=5)
        return "chrome.exe" in output.stdout
    except Exception:
        return None


def setup_driver():
    print("  Iniciando Chrome com seu perfil real...")
    options = Options()
    options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-search-engine-choice-screen")

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
        time.sleep(3)
        ext_id = driver.execute_script("""
            const mgr = document.querySelector('extensions-manager');
            if (!mgr) return null;
            const root = mgr.shadowRoot;
            const itemsList = root.querySelector('#itemsList');
            if (!itemsList) return null;
            const iroot = itemsList.shadowRoot;
            const items = iroot.querySelectorAll('extensions-item');
            for (let item of items) {
                const name = item.getAttribute('name') || '';
                if (name.toLowerCase().includes('navinclud')) {
                    return item.getAttribute('id');
                }
            }
            return null;
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


def wait_for_new_window(driver, known_handles, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = set(driver.window_handles)
        new_handles = current - known_handles
        if new_handles:
            return list(new_handles)
        time.sleep(0.5)
    return []


def run_single_test(driver, ext_id, student, main_handle, reused_wizard=False):
    wizard_url = f"chrome-extension://{ext_id}/wizard.html"
    wait = WebDriverWait(driver, 15)

    if not reused_wizard:
        known_handles = set(driver.window_handles)
        driver.execute_script(f"window.open('{wizard_url}', '_blank', 'width=420,height=600');")
        new_handles = wait_for_new_window(driver, known_handles)
        if not new_handles:
            print("ERRO: Janela do wizard nao abriu.")
            return False
        driver.switch_to.window(new_handles[0])
    else:
        if driver.current_url != wizard_url:
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
        if student["is_defective"]:
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

        wiz_handle = driver.current_window_handle

        driver.find_element(By.ID, "start-experience-btn").click()

        deadline = time.time() + 15
        exp_window_found = False
        while time.time() < deadline:
            try:
                for h in driver.window_handles:
                    if h == main_handle or h == wiz_handle:
                        continue
                    try:
                        driver.switch_to.window(h)
                        if "experience.html" in driver.current_url:
                            exp_window_found = True
                            break
                    except (NoSuchWindowException, WebDriverException):
                        continue
                if exp_window_found:
                    break
            except WebDriverException:
                pass
            time.sleep(0.5)

        if not exp_window_found:
            print("ERRO: Janela de experiencia nao encontrada.")
            return False

        try:
            wait.until(EC.presence_of_element_located((By.ID, "exit-experience-btn")))
        except TimeoutException:
            pass

        time.sleep(random.uniform(5, 10))

        try:
            driver.find_element(By.ID, "exit-experience-btn").click()
        except NoSuchElementException:
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

        time.sleep(7)

        driver.switch_to.window(main_handle)
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
        return True


def save_progress(completed_classes):
    data = {"completed_classes": completed_classes, "timestamp": time.time()}
    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def load_progress():
    try:
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"completed_classes": [], "timestamp": 0}


def main():
    print("=" * 55)
    print("  NAVINCLUD - SIMULADOR DE TESTES PARA 5 SALAS")
    print("  Total: 100 alunos | Salas: 3A 3B 2A 2B 1A")
    print("=" * 55)

    chrome_status = is_chrome_running()
    if chrome_status is True:
        print("\n  [!] Chrome esta ABERTO. Feche-o completamente antes de continuar.")
        print("  Pressione Enter apos fechar o Chrome...")
        input()
        chrome_status = is_chrome_running()
        if chrome_status is True:
            print("\n  Chrome ainda esta rodando. Feche manualmente e reinicie.")
            sys.exit(1)
    elif chrome_status is None:
        print("\n  (Nao foi possivel verificar se o Chrome esta rodando)")

    progress = load_progress()
    completed = set(progress.get("completed_classes", []))

    driver = setup_driver()
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

        for class_name in CLASSES_ORDER:
            if class_name in completed:
                print(f"  Sala {class_name} ja completada (pulando).")
                continue

            config = CLASSES[class_name]
            estudantes = generate_students(config, class_name)
            num_defect = sum(1 for s in estudantes if s["is_defective"])

            print(f"{'='*50}")
            print(f"  SALA {class_name}: {config['total']} alunos "
                  f"({config['males']}M/{config['total']-config['males']}F)"
                  f"  |  {num_defect} com diagnostico")
            print(f"{'='*50}")

            reused = False

            for idx, student in enumerate(estudantes, 1):
                turma_display = student["turma"]
                sexo_display = "M" if student["sexo"] == "Masculino" else "F"
                idade_display = student["idade"]
                defect_str = f" [{student['defect_type']}]" if student["is_defective"] else ""
                print(f"    [{idx:2d}/{config['total']}] "
                      f"{turma_display} | {sexo_display} | {idade_display:2d}a"
                      f"{defect_str} ... ", end="", flush=True)

                try:
                    ok = run_single_test(driver, ext_id, student,
                                         main_handle, reused_wizard=reused)
                    if not ok:
                        print("FALHA")
                        sys.exit(1)
                    reused = not student["is_defective"]
                    print("OK")
                except KeyboardInterrupt:
                    print("\n\n  Interrompido pelo usuario.")
                    save_progress(list(completed))
                    driver.quit()
                    sys.exit(0)
                except Exception as e:
                    print(f"ERRO: {e}")
                    save_progress(list(completed))
                    driver.quit()
                    sys.exit(1)

            completed.add(class_name)
            save_progress(list(completed))

            if class_name != CLASSES_ORDER[-1]:
                print()
                input("  >>> SALA CONCLUIDA! Faca o EXPORT manual no popup,")
                input("  >>> depois pressione Enter para continuar...")
                driver.switch_to.window(main_handle)
                print()

        print(f"\n{'='*55}")
        print("  TODAS AS 5 SALAS CONCLUIDAS COM SUCESSO!")
        print(f"  100 alunos simulados | 7 diagnosticados")
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
