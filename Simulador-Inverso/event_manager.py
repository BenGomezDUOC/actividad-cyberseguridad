import csv
import io
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

class EventManager:
    """
    Gestor de eventos y alertas de seguridad.
    RF-10: Registrar cada evento con fecha y hora.
    RF-11: Distinguir eventos normales de alertas.
    RF-13: Exportar los registros en formato CSV.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self.events: List[Dict[str, Any]] = []
        self._counter = 1

    def log_event(
        self,
        event_type: str,
        command: str,
        source: str,
        destination: str,
        category: str,
        level: str,
        details: str,
        response: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registra un evento en memoria.
        level: 'INFO', 'WARNING', 'CRITICAL', etc.
        category: 'NORMAL', 'ALERTA'
        """
        with self._lock:
            event = {
                "id": self._counter,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": event_type,
                "command": command,
                "source": source,
                "destination": destination,
                "category": category,
                "level": level,
                "details": details,
                "response": response or ""
            }
            self._counter += 1
            self.events.append(event)
            return event

    def get_events(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if limit:
                return list(reversed(self.events[-limit:]))
            return list(reversed(self.events))

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self.events)
            alerts = sum(1 for e in self.events if e["category"] == "ALERTA")
            normal = total - alerts
            critical = sum(1 for e in self.events if e["level"] == "CRITICAL")
            return {
                "total": total,
                "normal": normal,
                "alerts": alerts,
                "critical": critical
            }

    def clear(self):
        with self._lock:
            self.events.clear()
            self._counter = 1

    def export_csv(self) -> str:
        """
        Exporta todos los registros en formato CSV.
        """
        with self._lock:
            output = io.StringIO()
            fieldnames = [
                "id", "timestamp", "event_type", "command",
                "source", "destination", "category", "level",
                "details", "response"
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for evt in self.events:
                writer.writerow(evt)
            return output.getvalue()
