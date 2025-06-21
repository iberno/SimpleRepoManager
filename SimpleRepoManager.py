import customtkinter as ctk
import requests
import subprocess
import os
import shutil
import json
from pathlib import Path
from tkinter import messagebox

# Aparência e tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Diretórios e arquivos
CONFIG_PATH = Path("config.json")
BACKUP_DIR = Path.home() / "Documentos" / "SimpleRepoBackups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Estado global
USERNAME = ""
TOKEN = ""
REPOS = []
LOG_EXCLUIDOS = []

def get_headers():
    return {"Authorization": f"token {TOKEN}"}

def salvar_config():
    with open(CONFIG_PATH, "w") as f:
        json.dump({"username": USERNAME, "token": TOKEN}, f)

def carregar_config():
    global USERNAME, TOKEN
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                dados = json.load(f)
                USERNAME = dados.get("username", "")
                TOKEN = dados.get("token", "")
        except:
            pass

def splash_screen():
    splash = ctk.CTk()
    splash.geometry("400x220")
    splash.title("Simple Repo Manager")
    ctk.CTkLabel(splash, text="🚀 Simple Repo Manager", font=("Segoe UI", 18, "bold")).pack(pady=(50, 10))
    barra = ctk.CTkProgressBar(splash, mode="indeterminate", width=260)
    barra.pack(pady=10)
    barra.start()
    ctk.CTkLabel(splash, text="Inicializando...", font=("Segoe UI", 12)).pack(pady=5)
    splash.after(2000, lambda: [splash.destroy(), tela_login()])
    splash.mainloop()

def tela_login():
    login = ctk.CTk()
    login.geometry("420x330")
    login.title("Login GitHub")

    frame = ctk.CTkFrame(login)
    frame.pack(pady=30, padx=30, fill="both", expand=True)

    ctk.CTkLabel(frame, text="🔐 Acesse sua conta GitHub", font=("Segoe UI", 16, "bold")).pack(pady=(10, 20))
    entry_user = ctk.CTkEntry(frame, placeholder_text="Usuário GitHub")
    entry_user.pack(pady=10)
    entry_token = ctk.CTkEntry(frame, placeholder_text="Token pessoal", show="*")
    entry_token.pack(pady=10)

    rodape = ctk.CTkLabel(frame, text="❤️ Feito com carinho por Iberno Hoffmann by Co‑Sensei", font=("Segoe UI", 10), text_color="#888888")
    rodape.pack(side="bottom", pady=10)

    def autenticar(event=None):
        global USERNAME, TOKEN, REPOS
        USERNAME = entry_user.get().strip()
        TOKEN = entry_token.get().strip()
        try:
            r = requests.get("https://api.github.com/user/repos?per_page=100&type=owner", headers=get_headers())
            if r.status_code in [401, 403]:
                raise Exception("Token inválido ou expirado. Por favor, gere um novo.")
            r.raise_for_status()
            REPOS.clear()
            for repo in r.json():
                REPOS.append({"name": repo["name"], "clone_url": repo["clone_url"]})
            salvar_config()
            login.destroy()
            tela_painel()
        except Exception as e:
            ctk.CTkLabel(frame, text=f"❌ {e}", text_color="red").pack()

    entry_token.bind("<Return>", autenticar)
    ctk.CTkButton(frame, text="Entrar", command=autenticar).pack(pady=20)

    carregar_config()
    if USERNAME and TOKEN:
        entry_user.insert(0, USERNAME)
        entry_token.insert(0, TOKEN)
        autenticar()

    login.mainloop()

def tela_painel():
    app = ctk.CTk()
    app.geometry("700x740")
    app.title("Painel - Simple Repo Manager")

    rodape = ctk.CTkLabel(app, text="❤️ Feito com carinho por Iberno Hoffmann by Co‑Sensei", font=("Segoe UI", 10), text_color="#888888")
    rodape.pack(side="bottom", pady=5)

    checks = {}
    frame_scroll = ctk.CTkScrollableFrame(app, label_text="📦 Repositórios disponíveis")
    frame_scroll.pack(padx=20, pady=20, fill="both", expand=True)

    status = ctk.CTkLabel(app, text="")
    status.pack()

    barra = ctk.CTkProgressBar(app, width=560)
    barra.pack(pady=5)
    barra.set(0)

    opt_backup = ctk.BooleanVar(value=True)
    opt_excluir = ctk.BooleanVar(value=False)
    ctk.CTkCheckBox(app, text="Fazer backup .zip", variable=opt_backup).pack(anchor="w", padx=40, pady=(10, 0))
    ctk.CTkCheckBox(app, text="Excluir repositórios após backup", variable=opt_excluir).pack(anchor="w", padx=40)

    def carregar_repos():
        for widget in frame_scroll.winfo_children():
            widget.destroy()
        checks.clear()
        for repo in REPOS:
            var = ctk.BooleanVar()
            box = ctk.CTkCheckBox(frame_scroll, text=repo["name"], variable=var)
            box.pack(anchor="w", padx=20, pady=5)
            checks[repo["name"]] = (var, repo["clone_url"], box)
        status.configure(text=f"{len(REPOS)} repositórios carregados.")

    def executar():
        selecionados = [(n, u) for n, (v, u, _) in checks.items() if v.get()]
        if not selecionados:
            status.configure(text="⚠️ Nenhum repositório selecionado.")
            return
        total = len(selecionados)
        LOG_EXCLUIDOS.clear()

        for i, (name, url) in enumerate(selecionados):
            repo_dir = BACKUP_DIR / name
            try:
                if opt_backup.get():
                    if repo_dir.exists():
                        resposta = messagebox.askyesno("Pasta existente", f"A pasta '{name}' já existe. Deseja substituir?")
                        if resposta:
                            shutil.rmtree(repo_dir, ignore_errors=True)
                        else:
                            continue
                    subprocess.run(["git", "clone", url, str(repo_dir)], check=True)
                    shutil.make_archive(str(repo_dir), "zip", str(repo_dir))
                    shutil.rmtree(repo_dir, ignore_errors=True)
                if opt_excluir.get():
                    r = requests.delete(f"https://api.github.com/repos/{USERNAME}/{name}", headers=get_headers())
                    if r.status_code == 204:
                        LOG_EXCLUIDOS.append(name)
                REPOS[:] = [r for r in REPOS if r["name"] != name]
                _, _, box = checks[name]
                box.destroy()
                del checks[name]
            except Exception as e:
                print(f"[Erro] {name}: {e}")
            barra.set((i + 1) / total)
            status.configure(text=f"{i + 1}/{total} concluído...")
            app.update_idletasks()

        if LOG_EXCLUIDOS:
            with open("repos_excluidos.log", "w") as f:
                f.write("\n".join(LOG_EXCLUIDOS))
        status.configure(text="✅ Ações finalizadas.")

    def recarregar():
        try:
            r = requests.get("https://api.github.com/user/repos?per_page=100&type=owner", headers=get_headers())
            r.raise_for_status()
            REPOS.clear()
            for repo in r.json():
                REPOS.append({"name": repo["name"], "clone_url": repo["clone_url"]})
            carregar_repos()
            barra.set(0)
            status.configure(text=f"🔄 Lista recarregada com {len(REPOS)} repositórios.")
        except Exception as e:
            status.configure(text=f"❌ Falha ao recarregar: {e}")

    ctk.CTkButton(app, text="Executar Ações", command=executar).pack(pady=10)
    ctk.CTkButton(app, text="🔄 Recarregar Repositórios", command=recarregar).pack()
    carregar_repos()
    app.mainloop()

if __name__ == "__main__":
    splash_screen()

