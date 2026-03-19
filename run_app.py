import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
    # Garante que o executável encontre o script principal mesmo após o dump do PyInstaller
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))

if __name__ == "__main__":
    # Configura os argumentos para o Streamlit rodar internamente
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("main_dashboard.py"),
        "--global.developmentMode=false",
        "--theme.base=light",
        "--theme.primaryColor=#1C4BA0",
        "--theme.backgroundColor=white",
        "--theme.secondaryBackgroundColor=#F0F2F6",
        "--theme.textColor=#1C4BA0"
    ]
    sys.exit(stcli.main())