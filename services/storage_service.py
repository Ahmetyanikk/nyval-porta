from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
import re

BASE_DIR = Path("data/uploads")

def _slugify(name: str) -> str:
    name = (name or "").strip().lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = re.sub(r"-{2,}", "-", name).strip("-")
    return name or "company"

@dataclass
class SavedFile:
    vault: str
    original_name: str
    saved_path: str
    size_bytes: int

def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def make_batch_root(company_name: str) -> Path:
    company = _slugify(company_name)
    batch = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    root = BASE_DIR / company / batch
    _ensure_dir(root)
    return root

def save_one(uploaded_file, dest_dir: Path, vault: str) -> SavedFile:
    _ensure_dir(dest_dir)
    dest_path = dest_dir / uploaded_file.name
    with open(dest_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    size = getattr(uploaded_file, "size", 0) or 0
    return SavedFile(
        vault=vault,
        original_name=uploaded_file.name,
        saved_path=str(dest_path),
        size_bytes=size,
    )

def save_vault_files(
    batch_root: Path,
    vault: str,
    files,  # UploadedFile or list[UploadedFile]
) -> List[SavedFile]:
    saved: List[SavedFile] = []
    vault_dir = batch_root / vault
    if files is None:
        return saved

    # invoices are list; ENEDIS/WMS are single
    if isinstance(files, list):
        for f in files:
            saved.append(save_one(f, vault_dir, vault))
    else:
        saved.append(save_one(files, vault_dir, vault))

    return saved