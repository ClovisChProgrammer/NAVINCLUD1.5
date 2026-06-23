"""
NAVINCLUD Snapshot System
Preserva estado funcional com 5 niveis de rollback via git.
Uso: python snapshot.py take -m "mensagem"
     python snapshot.py list
     python snapshot.py rollback N
"""
import os
import json
import subprocess
import sys
from datetime import datetime

SNAPSHOT_DIR = "snapshots"
INDEX_FILE = os.path.join(SNAPSHOT_DIR, "snapshot_index.json")
MAX_SNAPSHOTS = 5
GIT_DIR = os.path.dirname(os.path.abspath(__file__))


def _git(*args):
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True, cwd=GIT_DIR
    )
    if result.returncode != 0:
        print(f"[ERRO] git {' '.join(args)}: {result.stderr.strip()}")
        return None
    return result.stdout.strip()


def _load_index():
    if not os.path.exists(INDEX_FILE):
        return {"max_snapshots": MAX_SNAPSHOTS, "entries": []}
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_index(index):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def _get_modified_files():
    files = _git("diff", "--name-only", "HEAD")
    if files:
        return files.split("\n")
    return []


def take_snapshot(message=""):
    index = _load_index()
    entries = index["entries"]

    modified = _get_modified_files()
    if not modified:
        modified = _git("diff", "--staged", "--name-only")
        if modified:
            modified = modified.split("\n")
    if not modified:
        modified = []

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"[SNAPSHOT] {timestamp}"
    if message:
        commit_msg += f" | {message}"

    _git("add", "--all")
    hash_result = _git("commit", "-m", commit_msg)
    if hash_result is None:
        print("[!] Nada a commitar — nenhuma alteracao desde o ultimo snapshot.")
        return False

    commit_hash = hash_result
    entry = {
        "id": len(entries) + 1 if entries else 1,
        "timestamp": timestamp,
        "commit_hash": commit_hash,
        "message": message or "(sem mensagem)",
        "modified_files": modified
    }

    entries.append(entry)
    if len(entries) > MAX_SNAPSHOTS:
        removido = entries.pop(0)
        print(f"  [Prune] Snapshot #{removido['id']} removido (max {MAX_SNAPSHOTS})")

    index["entries"] = entries
    _save_index(index)
    print(f"[OK] Snapshot #{entry['id']} — {timestamp}")
    print(f"  Commit: {commit_hash}")
    print(f"  Arquivos: {len(modified)} alterados")
    for f in modified:
        print(f"    - {f}")
    return True


def list_snapshots():
    index = _load_index()
    entries = index["entries"]
    if not entries:
        print("Nenhum snapshot encontrado.")
        return
    print(f"{'#':<4} {'Data/Hora':<20} {'Commit':<10} {'Arquivos':<10} Mensagem")
    print("-" * 80)
    for e in entries:
        n_files = len(e["modified_files"])
        msg = e["message"][:50]
        print(f"{e['id']:<4} {e['timestamp']:<20} {e['commit_hash'][:8]:<10} {n_files:<10} {msg}")


def rollback(steps=1):
    index = _load_index()
    entries = index["entries"]
    if not entries:
        print("[ERRO] Nenhum snapshot disponivel para rollback.")
        return False
    if steps < 1 or steps > MAX_SNAPSHOTS:
        print(f"[ERRO] steps deve ser entre 1 e {MAX_SNAPSHOTS}")
        return False
    if steps > len(entries):
        print(f"[ERRO] So existem {len(entries)} snapshots. steps maximo={len(entries)}")
        return False

    target = entries[-steps]
    print(f"[INFO] Revertendo para snapshot #{target['id']} — {target['timestamp']}")
    print(f"  Commit: {target['commit_hash'][:8]} — {target['message']}")

    # Reverter cada commit do mais recente ate o target (exclusive)
    commits = [e["commit_hash"] for e in entries[-steps:]]
    for i, ch in enumerate(reversed(commits)):
        print(f"  Revertendo commit {ch[:8]}...")
        result = _git("revert", "--no-commit", ch)
        if result is None:
            print(f"[!] Conflitos ao reverter {ch[:8]}. Resolva manualmente.")
            return False

    print("[OK] Rollback concluido. Verifique o estado antes de continuar.")
    _git("status", "--short")
    return True


def main():
    if len(sys.argv) < 2:
        print("Uso: python snapshot.py take|list|rollback [args]")
        print("  take -m MSG     Tira snapshot com mensagem")
        print("  list            Lista snapshots")
        print("  rollback N      Reverte N snapshots (1-5)")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "take":
        msg = ""
        if "-m" in sys.argv:
            idx = sys.argv.index("-m")
            if idx + 1 < len(sys.argv):
                msg = sys.argv[idx + 1]
        take_snapshot(msg)
    elif cmd == "list":
        list_snapshots()
    elif cmd == "rollback":
        steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        rollback(steps)
    else:
        print(f"Comando desconhecido: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
