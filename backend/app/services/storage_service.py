from __future__ import annotations

import uuid
from pathlib import Path

from app.config import BACKEND_DIR, get_settings


class StorageService:
    """Almacenamiento local en dev; intercambiable por S3 en producción."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (BACKEND_DIR / "storage" / "uploads")
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, *, content: bytes, school_id: uuid.UUID, filename: str) -> str:
        safe_name = Path(filename).name.replace("..", "_")
        key = f"schools/{school_id}/{uuid.uuid4()}_{safe_name}"
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key

    def resolve_path(self, storage_key: str) -> Path:
        path = (self.root / storage_key).resolve()
        if not str(path).startswith(str(self.root.resolve())):
            raise ValueError("storage_key inválido")
        return path

    def exists(self, storage_key: str) -> bool:
        return self.resolve_path(storage_key).is_file()


def get_storage() -> StorageService:
    settings = get_settings()
    root = Path(settings.storage_root) if getattr(settings, "storage_root", None) else None
    return StorageService(root=root)
