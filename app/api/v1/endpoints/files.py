import io
import logging
import zipfile

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["files"])


class FileNamesRequest(BaseModel):
    file_names: list[str]


class MarkedResponse(BaseModel):
    marked_now: int


@router.get("/files/names", response_model=list[str])
async def get_file_names() -> list[str]:
    download_path = settings.download_path
    if not download_path.exists():
        return []
    return sorted(
        f.name
        for f in download_path.iterdir()
        if f.is_file() and f.suffix == ".txt"
    )


@router.post("/files/download")
async def download_files(body: FileNamesRequest):
    download_path = settings.download_path
    buf = io.BytesIO()
    found = False
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in body.file_names:
            fp = download_path / name
            if fp.exists() and fp.is_file():
                zf.write(fp, name)
                found = True
    if not found:
        raise HTTPException(status_code=404, detail="No requested files found")
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=files.zip"},
    )


@router.post("/files/downloaded", response_model=MarkedResponse)
async def mark_downloaded(body: FileNamesRequest) -> MarkedResponse:
    download_path = settings.download_path
    marked = 0
    for name in body.file_names:
        fp = download_path / name
        if fp.exists():
            marked += 1
    return MarkedResponse(marked_now=marked)
