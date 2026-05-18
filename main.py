"""
Entrypoint ASGI: instancia la aplicación y expone `app` para Uvicorn.

Desarrollo (recomendado si `uvicorn` no está en el PATH, p. ej. Git Bash en Windows):

    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

Alternativas:

    python main.py
    chatbot-api

Tras `pip install -e .`, el ejecutable `uvicorn` debería existir en el entorno activo.
"""

from app.factory import create_app

app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
