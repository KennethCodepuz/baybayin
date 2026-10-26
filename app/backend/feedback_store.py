"""Short-lived, safe feedback contexts; never stores handwriting data."""

from datetime import datetime, timedelta, timezone
import secrets


class FeedbackResultStore:
    def __init__(self, ttl_minutes=10):
        self.ttl = timedelta(minutes=ttl_minutes)
        self.items = {}

    def put(self, value):
        now = datetime.now(timezone.utc)
        self.items = {key: item for key, item in self.items.items() if item['expiresAt'] > now}
        key = secrets.token_urlsafe(18)
        self.items[key] = {'value': value, 'expiresAt': now + self.ttl}
        return key

    def get(self, key):
        item = self.items.get(key)
        if not item or item['expiresAt'] <= datetime.now(timezone.utc):
            self.items.pop(key, None)
            return None
        return item['value']
