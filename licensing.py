"""convert-img · límite de conversiones de la versión gratuita.

Dos formas de guardar el contador (variable CONVERT_IMG_COUNTER):
  session (por defecto) -> por sesión del navegador. Se reinicia al recargar la página.
  file                  -> archivos firmados (HMAC) en el servidor (2 copias), compartidos por todos los usuarios.
                           Útil para una instalación local de un solo usuario.
Es un freno básico, no un sistema de licencias.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path

LIMIT = int(os.getenv("CONVERT_IMG_LIMIT", "300"))
_SECRET = os.getenv("CONVERT_IMG_SECRET", "MargaritaIT|convert-img|free|v1").encode()


def _sign(n: int) -> str:
    return hmac.new(_SECRET, str(n).encode(), hashlib.sha256).hexdigest()


class MemoryStore:
    """Contador en un diccionario (st.session_state o un dict simple)."""

    def __init__(self, backing: dict, key: str = "usage_count"):
        self.b, self.key = backing, key

    def read(self) -> int:
        return int(self.b.get(self.key, 0))

    def write(self, n: int) -> None:
        self.b[self.key] = int(n)


class FileStore:
    """Contador firmado en disco, guardado en dos ubicaciones (carpeta del usuario y carpeta de la app).
    Se toma el mayor valor entre las copias con firma válida; las alteradas se ignoran."""

    def __init__(self, *paths: str | os.PathLike):
        self.paths = [Path(p) for p in paths] or [
            Path.home() / ".convert-img" / "usage.json",
            Path(__file__).resolve().parent / ".usage.json",
        ]

    def read(self) -> int:
        best = 0
        for p in self.paths:
            try:
                d = json.loads(p.read_text("utf-8"))
                n = d["n"]
                if isinstance(n, int) and n >= 0 and hmac.compare_digest(d["s"], _sign(n)):
                    best = max(best, n)
            except Exception:
                pass
        return best

    def write(self, n: int) -> None:
        data = json.dumps({"n": n, "s": _sign(n)})
        for p in self.paths:
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(data, "utf-8")
            except OSError:
                pass


def info(store, limit: int = LIMIT) -> dict:
    used = store.read()
    return {"used": min(used, limit), "limit": limit, "remaining": max(0, limit - used)}


def consume(store, limit: int = LIMIT) -> bool:
    """Descuenta una conversión. Devuelve False si ya se alcanzó el límite."""
    used = store.read()
    if used >= limit:
        return False
    store.write(used + 1)
    return True


def reset(store) -> None:
    store.write(0)
