from __future__ import annotations

from dataclasses import dataclass

from config import HISTORY_FILE
from cache.utils import JsonStore, now_iso


@dataclass
class HistoryStore:
    store: JsonStore

    @classmethod
    def from_default(cls) -> "HistoryStore":
        return cls(JsonStore(HISTORY_FILE, default={}))

    def load(self) -> dict[str, dict[str, object]]:
        payload = self.store.load()
        return payload if isinstance(payload, dict) else {}

    def save(self, data: dict[str, dict[str, object]]) -> None:
        self.store.save(data)

    def get_user(self, user_id: int) -> dict[str, object] | None:
        return self.load().get(str(user_id))

    def create_user(self, user_id: int, name: str, username: str | None) -> dict[str, object]:
        timestamp = now_iso()
        return {
            "id": user_id,
            "name": name,
            "username": username,
            "messages": 0,
            "best_score": 0,
            "services": {},
            "groups": {},
            "history": [],
            "created": timestamp,
            "last_seen": timestamp,
            "vip": False,
        }

    def register_lead(
        self,
        *,
        user_id: int,
        name: str,
        username: str | None,
        group: str,
        services: list[str],
        score: int,
        message: str,
        level: str,
        category: str,
    ) -> dict[str, object]:
        data = self.load()
        key = str(user_id)
        user = data.get(key) or self.create_user(user_id, name, username)

        user["name"] = name
        user["username"] = username
        user["messages"] = int(user.get("messages", 0)) + 1
        user["last_seen"] = now_iso()
        user["best_score"] = max(int(user.get("best_score", 0)), score)
        user["vip"] = bool(user.get("vip")) or level == "VIP"

        service_map = dict(user.get("services", {}))
        for service in services or ["general"]:
            service_map[service] = int(service_map.get(service, 0)) + 1
        user["services"] = service_map

        group_map = dict(user.get("groups", {}))
        group_map[group] = int(group_map.get(group, 0)) + 1
        user["groups"] = group_map

        history = list(user.get("history", []))
        history.append(
            {
                "date": now_iso(),
                "services": services or ["general"],
                "score": score,
                "group": group,
                "category": category,
                "message": message,
            }
        )
        user["history"] = history[-200:]
        data[key] = user
        self.save(data)
        return user

    def summary(self, user_id: int) -> dict[str, object] | None:
        user = self.get_user(user_id)
        if not user:
            return None
        services = dict(user.get("services", {}))
        groups = dict(user.get("groups", {}))
        return {
            "id": user["id"],
            "name": user.get("name"),
            "username": user.get("username"),
            "messages": int(user.get("messages", 0)),
            "best_score": int(user.get("best_score", 0)),
            "favorite_service": max(services, key=services.get) if services else None,
            "favorite_group": max(groups, key=groups.get) if groups else None,
            "last_seen": user.get("last_seen"),
            "vip": bool(user.get("vip", False)),
        }

    def top_users(self, limit: int = 10) -> list[dict[str, object]]:
        users = list(self.load().values())
        users.sort(key=lambda item: (int(item.get("best_score", 0)), int(item.get("messages", 0))), reverse=True)
        return users[:limit]

    def aggregate_services(self) -> dict[str, int]:
        output: dict[str, int] = {}
        for user in self.load().values():
            for service, count in dict(user.get("services", {})).items():
                output[service] = output.get(service, 0) + int(count)
        return dict(sorted(output.items(), key=lambda item: item[1], reverse=True))

    def aggregate_groups(self) -> dict[str, int]:
        output: dict[str, int] = {}
        for user in self.load().values():
            for group, count in dict(user.get("groups", {})).items():
                output[group] = output.get(group, 0) + int(count)
        return dict(sorted(output.items(), key=lambda item: item[1], reverse=True))

    def stats(self) -> dict[str, int]:
        users = list(self.load().values())
        return {
            "users": len(users),
            "messages": sum(int(user.get("messages", 0)) for user in users),
            "vip": sum(1 for user in users if bool(user.get("vip", False))),
            "recurrent": sum(1 for user in users if int(user.get("messages", 0)) >= 3),
            "services": len(self.aggregate_services()),
            "groups": len(self.aggregate_groups()),
        }


__all__ = ["HistoryStore"]
