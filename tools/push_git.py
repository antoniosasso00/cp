import subprocess
import sys

def run_cmd(command: list[str], exit_on_error=True):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore durante l'esecuzione: {' '.join(command)}")
        if exit_on_error:
            sys.exit(1)

def main():
    print("📤 Script di push Git automatizzato\n")

    commit_message = input("✏️  Inserisci il messaggio del commit: ").strip()
    if not commit_message:
        print("❌ Il messaggio del commit non può essere vuoto.")
        sys.exit(1)

    print("\n📁 Aggiunta di tutti i file modificati...")
    run_cmd(["git", "add", "."])

    print("📝 Creazione del commit...")
    run_cmd(["git", "commit", "-m", commit_message])

    print("🚀 Push su 'origin/main' con tag...")
    run_cmd(["git", "push", "origin", "main", "--tags"])

    print("\n✅ Push completato con successo!")

if __name__ == "__main__":
    main()
