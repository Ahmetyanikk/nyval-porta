#validation_service.py
from __future__ import annotations

MAX_MB_DEFAULT = 25

def _size_ok(file, max_mb: int) -> bool:
    # Streamlit UploadedFile has .size in bytes
    size = getattr(file, "size", None)
    if size is None:
        return True
    return size <= max_mb * 1024 * 1024

def validate_single_upload(file, allowed_exts: tuple[str, ...], max_mb: int = MAX_MB_DEFAULT) -> list[str]:
    errors = []
    if file is None:
        errors.append("File is required.")
        return errors

    name = (getattr(file, "name", "") or "").lower().strip()
    if not any(name.endswith(ext) for ext in allowed_exts):
        errors.append(f"Invalid file type. Allowed: {', '.join(allowed_exts)}")

    if not _size_ok(file, max_mb):
        size_mb = round(file.size / (1024 * 1024), 2)
        errors.append(f"{file.name}: {size_mb} MB exceeds the {max_mb} MB limit. Please upload a smaller file.")
    return errors
def validate_multi_upload(files, allowed_exts: tuple[str, ...], max_mb: int = MAX_MB_DEFAULT) -> list[str]:
    errors = []
    if not files:
        errors.append("At least one file is required.")
        return errors

    for f in files:
        name = (getattr(f, "name", "") or "").lower().strip()
        if not any(name.endswith(ext) for ext in allowed_exts):
            errors.append(f"{f.name}: invalid type (allowed: {', '.join(allowed_exts)})")
        elif not _size_ok(f, max_mb):
            size_mb = round(f.size / (1024 * 1024), 2)
            errors.append(f"{f.name}: {size_mb} MB exceeds the {max_mb} MB limit. Please upload a smaller file.")
    return errors