"""calendar_backend.py - A dependency-free calendar engine with JSON persistence."""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calendar_data.json")


@dataclass
class Event:
    id: int
    title: str
    date: str
    kind: str
    notes: str = ""
    resolved: bool = False
    result: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Event":
        required = ["id", "title", "date", "kind"]
        for f in required:
            if f not in d:
                raise ValueError(f"Missing required field: {f}")
        datetime.strptime(d["date"], "%Y-%m-%d")
        return Event(**d)


class CalendarBackend:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._events: List[Event] = []
        self._next_id = 1
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.db_path):
            self._events = []
            self._next_id = 1
            return

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._events = [Event.from_dict(e) for e in raw.get("events", [])]
            self._next_id = raw.get("next_id", 1)
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Warning: Failed to load data from {self.db_path}: {e}")
            self._events = []
            self._next_id = 1

    def _save(self) -> None:
        payload = {
            "next_id": self._next_id,
            "events": [e.to_dict() for e in self._events],
        }
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def add_event(self, title: str, on_date: str, kind: str,
                  notes: str = "", result: Optional[str] = None) -> Event:
        datetime.strptime(on_date, "%Y-%m-%d")
        ev = Event(
            id=self._next_id,
            title=title,
            date=on_date,
            kind=kind,
            notes=notes,
            result=result
        )
        self._events.append(ev)
        self._next_id += 1
        self._save()
        return ev

    def remove_event(self, event_id: int) -> bool:
        initial_len = len(self._events)
        self._events = [e for e in self._events if e.id != event_id]
        if len(self._events) != initial_len:
            self._save()
            return True
        return False

    def get_event(self, event_id: int) -> Optional[Event]:
        for ev in self._events:
            if ev.id == event_id:
                return ev
        return None

    def update_event(self, event_id: int, **kwargs) -> bool:
        ev = self.get_event(event_id)
        if not ev:
            return False

        for key, val in kwargs.items():
            if key == "id":
                continue
            if hasattr(ev, key):
                if key == "date":
                    datetime.strptime(val, "%Y-%m-%d")
                setattr(ev, key, val)

        self._save()
        return True

    def toggle_resolved(self, event_id: int) -> bool:
        ev = self.get_event(event_id)
        if not ev:
            return False
        ev.resolved = not ev.resolved
        self._save()
        return True

    def list_events(self, kind: Optional[str] = None,
                   resolved: Optional[bool] = None) -> List[Event]:
        result = self._events[:]
        if kind is not None:
            result = [e for e in result if e.kind == kind]
        if resolved is not None:
            result = [e for e in result if e.resolved == resolved]
        return sorted(result, key=lambda e: e.date)

    def get_by_date(self, date_str: str) -> List[Event]:
        datetime.strptime(date_str, "%Y-%m-%d")
        return [e for e in self._events if e.date == date_str]

    def search(self, query: str) -> List[Event]:
        q = query.lower()
        return [e for e in self._events
                if q in e.title.lower() or q in e.notes.lower()]

    def count(self, kind: Optional[str] = None) -> int:
        if kind is None:
            return len(self._events)
        return sum(1 for e in self._events if e.kind == kind)

    def clear(self) -> None:
        self._events = []
        self._next_id = 1
        self._save()

    @property
    def events(self) -> List[Event]:
        return self._events.copy()

    def __len__(self) -> int:
        return len(self._events)

    def __repr__(self) -> str:
        return f"<CalendarBackend events={len(self._events)}>"


if __name__ == "__main__":
    print("CalendarBackend module - import and use in your own code.")
