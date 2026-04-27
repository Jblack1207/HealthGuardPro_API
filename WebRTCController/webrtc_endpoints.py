import json
import os
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from firebase_admin import auth
from sqlalchemy import select

from db import AsyncSessionLocal
from DataModels.DeviceLinkModel import DeviceLink
from DataModels.DeviceModel import Device
from DataModels.UserModel import User

router = APIRouter(prefix="/webrtc", tags=["WebRTC"])

rooms: dict[str, dict[str, WebSocket]] = defaultdict(dict)


async def get_user_from_firebase_token(token: str) -> User | None:
    try:
        decoded = auth.verify_id_token(token)
    except Exception:
        return None

    firebase_uid = decoded.get("uid")
    if not firebase_uid:
        return None

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.firebase_uid == firebase_uid)
        )
        return result.scalar_one_or_none()


async def user_has_device_access(user_id: int, device_id: str) -> bool:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(DeviceLink)
            .join(Device, Device.id == DeviceLink.device_pk)
            .where(Device.device_id == device_id, DeviceLink.user_id == user_id)
        )
        return result.scalar_one_or_none() is not None


@router.websocket("/device/{device_id}")
async def device_socket(websocket: WebSocket, device_id: str):
    api_key = websocket.headers.get("x-api-key")
    expected_api_key = os.getenv("API_KEY")

    print("device websocket hit:", device_id)
    print("received x-api-key:", api_key)
    print("expected key exists:", expected_api_key is not None)

    if not api_key or not expected_api_key or api_key != expected_api_key:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    rooms[device_id]["device"] = websocket

    try:
        while True:
            raw = await websocket.receive_text()
            viewer = rooms[device_id].get("viewer")
            if viewer:
                await viewer.send_text(raw)
    except WebSocketDisconnect:
        pass
    finally:
        if rooms.get(device_id, {}).get("device") is websocket:
            del rooms[device_id]["device"]
        if not rooms.get(device_id):
            rooms.pop(device_id, None)


@router.websocket("/view/{device_id}")
async def viewer_socket(websocket: WebSocket, device_id: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    user = await get_user_from_firebase_token(token)
    if not user:
        await websocket.close(code=1008)
        return

    has_access = await user_has_device_access(user.id, device_id)
    if not has_access:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    rooms[device_id]["viewer"] = websocket

    try:
        while True:
            raw = await websocket.receive_text()
            device = rooms[device_id].get("device")
            if device:
                await device.send_text(raw)
    except WebSocketDisconnect:
        pass
    finally:
        if rooms.get(device_id, {}).get("viewer") is websocket:
            del rooms[device_id]["viewer"]
        if not rooms.get(device_id):
            rooms.pop(device_id, None)

            
@router.get("/ping")
async def ping():
    return {"ok": True}

