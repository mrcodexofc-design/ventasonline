from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from config import TRENDS_FILE
from cache.utils import JsonStore


@dataclass
class TrendDetector:
    store: JsonStore

    @classmethod
    def from_default(cls) -> "TrendDetector":
        return cls(JsonStore(TRENDS_FILE, default={}))

    def load(self) -> dict[str, object]:
        payload = self.store.load()
        return payload if isinstance(payload, dict) else {}

    def register(self, services: list[str], group: str) -> dict[str, object]:
        payload = self.load()
        service_trends = dict(payload.get("services", {}))
        for service in services or ["general"]:
            service_trends[service] = int(service_trends.get(service, 0)) + 1
        payload["services"] = service_trends

        group_trends = dict(payload.get("groups", {}))
        group_trends[group] = int(group_trends.get(group, 0)) + 1
        payload["groups"] = group_trends

        payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self.store.save(payload)
        return payload

    def top_services(self, limit: int = 10) -> dict[str, int]:
        services = dict(self.load().get("services", {}))
        ordered = sorted(services.items(), key=lambda item: item[1], reverse=True)
        return dict(ordered[:limit])

    def top_groups(self, limit: int = 10) -> dict[str, int]:
        groups = dict(self.load().get("groups", {}))
        ordered = sorted(groups.items(), key=lambda item: item[1], reverse=True)
        return dict(ordered[:limit])


__all__ = ["TrendDetector"]
