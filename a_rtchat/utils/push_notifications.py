import json
from pywebpush import webpush, WebPushException
from django.conf import settings
from urllib.parse import urlparse

from a_rtchat.models import ChatGroup
def send_push_notification(subscription, payload) -> bool:
    print(f"Sending push notification with payload: {payload}")  # Log the payload
    try:    
        
        endpoint = subscription.endpoint
        aud = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(endpoint))
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth,
                },
            },
            data=payload,
            vapid_private_key=settings.WEBPUSH_SETTINGS['VAPID_PRIVATE_KEY'],
            vapid_claims={
                "sub": settings.WEBPUSH_SETTINGS['VAPID_ADMIN_EMAIL'],
                "aud": aud,
            }
        )
        return True
    except WebPushException as ex:
        print(f"Web push failed: {repr(ex)}")
        # Remove expired/invalid subscriptions (HTTP 404/410)
        try:
            status = getattr(ex.response, 'status_code', None)
        except Exception:
            status = None
        if status in (404, 410):
            subscription.delete()
            print("Deleted expired push subscription")
        return False


def notify_users_about_message(message):
    from ..models import PushSubscription

    print(f" notify_users_about_message called for message from {message.author.username}")
    print(f" Chat group: {message.group.group_name}")
    print(f" All group members: {[u.username for u in message.group.members.all()]}")

    group_members = message.group.members.exclude(id=message.author.id)
    online_users = ChatGroup.objects.get(group_name="online-status").users_online.all()
    subscriptions = PushSubscription.objects.filter(user__in=group_members & online_users)


    if subscriptions.count() == 0:
        print(" No push subscriptions found for any group members")
        return
    
    # Create better payload with proper icon handling
    icon_url = "/static/images/ape1.jpg"  # Default icon
    try:
        if hasattr(message.author, 'profile') and message.author.profile.avatar:
            icon_url = message.author.profile.avatar.url
    except:
        pass
    
    payload = json.dumps({
        "title": f"New message from {message.author.username}",
        "body": message.body or "Sent a file",
        "icon": icon_url,
        "url": f"/chat/room/{message.group.group_name}/",
    })
    
    print(f" Sending notification to {subscriptions.count()} users in group {message.group.group_name}")
    print(f" Payload: {payload}")

    for subscription in subscriptions:
        print(f" Sending notification to {subscription.user.username}")
        result = send_push_notification(subscription, payload)
        print(f" Notification sent successfully: {result}" if result else f" Notification failed for {subscription.user.username}")

