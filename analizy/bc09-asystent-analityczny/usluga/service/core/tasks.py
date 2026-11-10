"""Magazyn zadań. Asystent może tylko tworzyć SZKICE. Zatwierdzenie to osobna funkcja `approve_task`,
która NIE jest zarejestrowana w narzędziach modelu (patrz tools.TOOL_REGISTRY) i wymaga zatwierdzającego człowieka."""
import json
from datetime import datetime, timezone
from pathlib import Path

from . import config


class TaskStore:
    def __init__(self, path=config.TASKS_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _load(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, items):
        self.path.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")

    def propose(self, title, description, owner):
        items = self._load()
        t = {"id": len(items) + 1, "title": str(title)[:200], "description": str(description)[:2000],
             "owner": str(owner)[:100], "status": "szkic", "created_by": "asystent",
             "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        items.append(t)
        self._save(items)
        return t

    def list(self):
        return self._load()


def approve_task(store: TaskStore, task_id: int, approver: str):
    """Tylko dla człowieka (np. CLI/UI zatwierdzającego). Model nie ma do tej funkcji dostępu."""
    if not approver or not approver.strip():
        raise PermissionError("Zatwierdzenie wymaga nazwiska zatwierdzającego.")
    items = store._load()
    for t in items:
        if t["id"] == task_id:
            t["status"] = "zatwierdzone"
            t["approved_by"] = approver.strip()
            store._save(items)
            return t
    raise KeyError(f"Brak zadania {task_id}")
