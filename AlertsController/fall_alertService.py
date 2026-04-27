from datetime import datetime, timedelta

from sqlalchemy import select, and_

from db import AsyncSessionLocal
from DataModels.AlertModel import Alert
from DataModels.FallDetectionModel import FallReading as FallEvent
from .alert_helper import get_user_ids_for_device

ALERT_TYPE = "fall_detected"
SOURCE_TABLE = "fall_events"
FALL_ALERT_COOLDOWN_SECONDS = 15


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
                            Alert.status.in_(["active", "acknowledged"]),
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
                    status="active",
                    source_table=SOURCE_TABLE,
                    source_row_id=event.id,
                )
                db.add(alert)
                await db.flush()

                created_alert_id = alert.id

            event.alert_processed = True
            event.alert_processed_at = datetime.utcnow()
            event.alert_id = created_alert_id

        await db.commit()
