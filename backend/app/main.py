import os
from datetime import datetime, timezone

import psycopg2
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# APP_VERSION vem do ambiente. Mudar esse valor e dar push e o jeito mais
# facil de provar que o deploy automatico funcionou (a versao muda na tela).
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://demo:demo@db:5432/demo")

app = FastAPI(title="DevOps Demo API", version=APP_VERSION)


def check_database() -> bool:
    """Tenta abrir uma conexao com o Postgres. Da sentido ao status:
    o endpoint reflete o estado real de uma dependencia."""
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=2)
        conn.close()
        return True
    except Exception:
        return False


@app.get("/api/status")
def status():
    db_ok = check_database()
    return JSONResponse(
        {
            "status": "ok",
            "service": "backend",
            "version": APP_VERSION,
            "database": "connected" if db_ok else "disconnected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


# Usado pelo healthcheck do container (nao depende do banco).
@app.get("/api/health")
def health():
    return {"status": "healthy"}
