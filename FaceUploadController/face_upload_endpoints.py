from pathlib import Path
import shutil
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Form, Header
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from AuthController.auth_dependencies import get_current_user
from db import get_db, AsyncSessionLocal
from DataModels.UserModel import User
from DataModels.DeviceLinkModel import DeviceLink
from DataModels.DeviceModel import Device

router = APIRouter(prefix="/faces", tags=["Faces"])

UPLOAD_ROOT = Path("/opt/IoTAppAPI/uploads/faces")


@router.post("/upload")
async def upload_face_images(
    person_name: str = Form(...),
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    safe_person_name = person_name.strip().replace(" ", "_").lower()
    if not safe_person_name:
        raise HTTPException(status_code=400, detail="person_name is required")

    user_folder = UPLOAD_ROOT / str(current_user.id) / safe_person_name
    user_folder.mkdir(parents=True, exist_ok=True)

    saved = []

    for file in files:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {file.filename}",
            )

        suffix = Path(file.filename).suffix.lower()
        filename = f"{uuid4().hex}{suffix}"
        destination = user_folder / filename

        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        saved.append({
            "filename": filename,
            "person_name": safe_person_name,
        })

    return {
        "message": "Face images uploaded successfully",
        "person_name": safe_person_name,
        "files": saved,
    }

@router.get("/me/files")
async def list_my_face_images(
    current_user: User = Depends(get_current_user),
):
    user_folder = UPLOAD_ROOT / str(current_user.id)
    user_folder.mkdir(parents=True, exist_ok=True)

    files = []
    for path in user_folder.iterdir():
        if path.is_file():
            files.append({
                "filename": path.name,
                "url": f"/faces/me/files/{path.name}",
            })

    return files


@router.get("/me/files/{filename}")
async def get_my_face_image(
    filename: str,
    current_user: User = Depends(get_current_user),
):
    path = UPLOAD_ROOT / str(current_user.id) / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path)


@router.get("/device/{device_id}/archive")
async def download_face_archive_for_device(device_id: str):
    async with AsyncSessionLocal() as db:
        device_result = await db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        device = device_result.scalar_one_or_none()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        link_result = await db.execute(
            select(DeviceLink).where(DeviceLink.device_pk == device.id)
        )
        device_link = link_result.scalar_one_or_none()

        if not device_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No linked user found for this device",
            )

        user_id = device_link.user_id

    user_folder = UPLOAD_ROOT / str(user_id)
    if not user_folder.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No face dataset found for linked user",
        )

    archive_path = UPLOAD_ROOT / f"{device_id}_faces.zip"
    shutil.make_archive(str(archive_path.with_suffix("")), "zip", user_folder)

    return FileResponse(
        archive_path,
        media_type="application/zip",
        filename=f"{device_id}_faces.zip",
    )
