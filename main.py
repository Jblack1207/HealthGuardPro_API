from contextlib import suppress
import asyncio

from fastapi import FastAPI
from AuthController.auth_endpoints import router as auth_router
from UserController.users_endpoints import router as users_router
from HeartRateController.hr_endpoints import router as hr_router
from DevicesController.device_endpoints import router as device_router
from WebRTCController.webrtc_endpoints import router as webrtc_router
from FaceUploadController.face_upload_endpoints import router as face_upload_router
from FallDetectionController.fall_detection_endpoints import router as fall_detection_router
from AlertsController.alerts_endpoints import router as alerts_router
from PushTokenController.pushtoken_endpoints import router as pushtoken_router
from AlertsController.fall_alertService import process_fall_alerts


from AuthController.auth_dependencies import init_firebase


app = FastAPI(title="IoT App API")

@app.on_event("startup")
def startup_event():
    init_firebase()

#auth routes
app.include_router(auth_router)

#users routes
app.include_router(users_router)

#hr routes
app.include_router(hr_router)

#device routes
app.include_router(device_router)

#webrtc routes
app.include_router(webrtc_router)

#face upload routes
app.include_router(face_upload_router)

#fall detection routes
app.include_router(fall_detection_router)

#alerts routes
app.include_router(alerts_router)

#push token routes
app.include_router(pushtoken_router)


fall_alert_task = None


async def fall_alert_worker():
    while True:
        try:
            await process_fall_alerts()
        except Exception as e:
            print("[WARN] Fall alert worker error:", e)

        await asyncio.sleep(5)


@app.on_event("startup")
async def startup_event():
    global fall_alert_task
    fall_alert_task = asyncio.create_task(fall_alert_worker())


@app.on_event("shutdown")
async def shutdown_event():
    global fall_alert_task
    if fall_alert_task:
        fall_alert_task.cancel()
        with suppress(asyncio.CancelledError):
            await fall_alert_task




# Uncomment for health check endpoint

# @app.get("/service/health-check", tags=["Service"])
# async def health_check(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(text("SELECT 1 AS ok;"))
#     row = result.mappings().first()
#     return {"db": row["ok"]}

