from firebase_admin import messaging

# Function to send push notification using Firebase Cloud Messaging
def send_push(push_token: str, title: str, body: str, data: dict[str, str] | None = None):
    message = messaging.Message(
        token=push_token,
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        android=messaging.AndroidConfig(priority="high"),
        apns=messaging.APNSConfig(
            headers={"apns-priority": "10"},
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound="default")
            ),
        ),
    )
    return messaging.send(message)
