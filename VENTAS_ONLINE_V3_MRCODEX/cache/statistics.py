from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from config import STATS_FILE
from cache.utils import JsonStore


def _today_key() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _hour_key() -> str:
    return datetime.now().strftime("%H:00")


@dataclass
class StatisticsStore:
    store: JsonStore

    @classmethod
    def from_default(cls) -> "StatisticsStore":
        return cls(JsonStore(STATS_FILE, default={}))

    def load(self) -> dict[str, object]:
        payload = self.store.load()
        return payload if isinstance(payload, dict) else {}

    def save(self, data: dict[str, object]) -> None:
        self.store.save(data)

    def register_lead(
        self,
        *,
        services: list[str],
        group: str,
        username: str | None,
        level: str,
    ) -> dict[str, object]:
        stats = self.load()
        stats["total_leads"] = int(stats.get("total_leads", 0)) + 1
        stats["vip_detected"] = int(stats.get("vip_detected", 0)) + (1 if level == "VIP" else 0)

        per_day = dict(stats.get("leads_per_day", {}))
        per_day[_today_key()] = int(per_day.get(_today_key(), 0)) + 1
        stats["leads_per_day"] = per_day

        per_hour = dict(stats.get("leads_per_hour", {}))
        per_hour[_hour_key()] = int(per_hour.get(_hour_key(), 0)) + 1
        stats["leads_per_hour"] = per_hour

        service_map = dict(stats.get("services", {}))
        for service in services or ["general"]:
            service_map[service] = int(service_map.get(service, 0)) + 1
        stats["services"] = service_map

        group_map = dict(stats.get("groups", {}))
        group_map[group] = int(group_map.get(group, 0)) + 1
        stats["groups"] = group_map

        user_map = dict(stats.get("users", {}))
        if username:
            user_map[username] = int(user_map.get(username, 0)) + 1
        stats["users"] = user_map

        self.save(stats)
        return stats

    def snapshot(self) -> dict[str, object]:
        stats = self.load()
        return {
            "total_leads": int(stats.get("total_leads", 0)),
            "vip_detected": int(stats.get("vip_detected", 0)),
            "today_leads": int(dict(stats.get("leads_per_day", {})).get(_today_key(), 0)),
            "active_services": len(dict(stats.get("services", {}))),
            "active_groups": len(dict(stats.get("groups", {}))),
            "recurrent_users": sum(1 for count in dict(stats.get("users", {})).values() if int(count) >= 2),
            "leads_per_day": dict(stats.get("leads_per_day", {})),
            "leads_per_hour": dict(stats.get("leads_per_hour", {})),
            "services": dict(stats.get("services", {})),
            "groups": dict(stats.get("groups", {})),
            "users": dict(stats.get("users", {})),
        }

    def summary_line(self) -> str:
        snapshot = self.snapshot()
        return (
            f"total={snapshot['total_leads']} | "
            f"vip={snapshot['vip_detected']} | "
            f"hoy={snapshot['today_leads']} | "
            f"servicios={snapshot['active_services']} | "
            f"grupos={snapshot['active_groups']} | "
            f"recurrentes={snapshot['recurrent_users']}"
        )


__all__ = ["StatisticsStore"]
