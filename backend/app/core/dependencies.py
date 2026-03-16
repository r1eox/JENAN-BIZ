"""
Common FastAPI dependencies — DB session, pagination, file validation.
"""

from fastapi import UploadFile, HTTPException, Query

from app.config import get_settings

settings = get_settings()


# ─── Pagination ─────────────────────────────────────────

class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="رقم الصفحة"),
        size: int = Query(20, ge=1, le=500, description="عدد العناصر"),
    ):
        self.page = page
        self.size = size
        self.offset = (page - 1) * size


# ─── File validation ───────────────────────────────────

ALLOWED_EXCEL = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
    "application/vnd.ms-excel",  # xls
    "application/pdf",  # pdf
}

ALLOWED_CR = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
}


async def validate_excel_file(file: UploadFile) -> UploadFile:
    """Validate an Excel bank statement upload."""
    if not file.filename:
        raise HTTPException(400, "لم يتم تحديد ملف")

    ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if ext not in ("xlsx", "xls", "pdf"):
        raise HTTPException(400, "يجب أن يكون الملف بصيغة Excel (.xlsx أو .xls) أو PDF")

    # Size check (read content to verify)
    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(400, f"حجم الملف يتجاوز الحد الأقصى ({settings.MAX_FILE_SIZE_MB} MB)")

    # Reset file position for downstream consumers
    await file.seek(0)
    return file


async def validate_cr_file(file: UploadFile) -> UploadFile:
    """Validate a CR document upload (PDF or image)."""
    if not file.filename:
        raise HTTPException(400, "لم يتم تحديد ملف")

    ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if ext not in ("pdf", "png", "jpg", "jpeg"):
        raise HTTPException(400, "يجب أن يكون الملف PDF أو صورة (PNG/JPG)")

    content = await file.read()
    max_bytes = 10 * 1024 * 1024  # 10 MB for CR
    if len(content) > max_bytes:
        raise HTTPException(400, "حجم ملف السجل التجاري يتجاوز 10 MB")

    await file.seek(0)
    return file
