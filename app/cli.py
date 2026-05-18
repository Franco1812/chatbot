"""Punto de entrada CLI (expuesto como script tras `pip install -e .`)."""


def dev() -> None:
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
