from datetime import datetime, timedelta

from sqlalchemy import select, and_

from PushTokenController.notification_service import send_push
from db import AsyncSessionLocal
from DataModels.AlertModel import Alert
from DataModels.FallDetectionModel import FallReading as FallEvent
from .alert_helper import get_push_tokens_for_user, get_user_ids_for_device

ALERT_TYPE = "fall_detected"
SOURCE_TABLE = "fall_events"
FALL_ALERT_COOLDOWN_SECONDS = 15

# Main function to process fall alerts, called by a background task when fall alert with possible_fall=1 is created
async def process_fall_alerts():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(FallEvent)
            .where(
                FallEvent.possible_fall == 1,
                FallEvent.alert_processed == False,
            )
            .order_by(FallEvent.id.asc())
        )
        events = result.scalars().all()

        if not events:
            return

        for event in events:
            user_ids = await get_user_ids_for_device(db, event.device_id)

            if not user_ids:
                event.alert_processed = True
                event.alert_processed_at = datetime.utcnow()
                continue

            created_alert_id = None

            for user_id in user_ids:
                cooldown_cutoff = datetime.utcnow() - timedelta(seconds=FALL_ALERT_COOLDOWN_SECONDS)

                existing_result = await db.execute(
                    select(Alert).where(
                        and_(
                            Alert.device_id == event.device_id,
                            Alert.user_id == user_id,
                            Alert.type == ALERT_TYPE,
                            Alert.status.in_(["Active", "Acknowledged"]),
                            Alert.created_at >= cooldown_cutoff,
                        )
                    )
                )
                existing_alert = existing_result.scalar_one_or_none()

                if existing_alert:
                    created_alert_id = existing_alert.id
                    continue

                alert = Alert(
                    device_id=event.device_id,
                    user_id=user_id,
                    type=ALERT_TYPE,
                    title="Fall Detected",
                    message="A possible fall has been detected for this device.",
                    severity="critical",
                    status="Active",
                    source_table=SOURCE_TABLE,
                    source_row_id=event.id,
                )
                db.add(alert)
                await db.flush()

                created_alert_id = alert.id

                push_tokens = await get_push_tokens_for_user(db, user_id)

    for push_token in push_tokens:
        try:
            send_push(
                push_token,
                "Fall Detected",
                "A possible fall has been detected for this device.",
                data={
                    "type": "fall_detected",
                    "alert_id": str(alert.id),
                    "device_id": event.device_id,
                },
            )
        except Exception as e:
            print("[WARN] Failed to send push:", e)

            event.alert_processed = True
            event.alert_processed_at = datetime.utcnow()
            event.alert_id = created_alert_id

            

        await db.commit()
