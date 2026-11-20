"""
event_manager.py
Gestor centralizado de eventos, clasificación de severidad y exportación CSV.
Cumple con RF-10, RF-11 y RF-13.
"""

import csv
import io
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

class EventManager:
    """
    Administrador thread-safe de registros de auditoría y alertas de seguridad.
    """
    def __init__(self):
        self._events: List[Dict[str, Any]] = []
        self._counter: int = 1
        self._lock = threading.Lock()

    def record_event(
        self,
        tipo: str,
        origen: str,
        destino: str,
        comando: str,
        descripcion: str,
        severidad: str = "INFO",
        es_alerta: bool = False,
        justificacion_defensiva: str = "Operación normal del sistema"
    ) -> Dict[str, Any]:
        """
        Registra un evento con marca temporal y clasificación de seguridad.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with self._lock:
            event = {
                "id": self._counter,
                "timestamp": timestamp,
                "tipo": tipo.upper(),
                "origen": origen.upper(),
                "destino": destino.upper(),
                "comando": comando.upper() if comando else "N/A",
                "descripcion": descripcion,
                "severidad": severidad.upper(),
                "es_alerta": es_alerta,
                "justificacion_defensiva": justificacion_defensiva
            }
            self._events.append(event)
            self._counter += 1
            return event

    def get_events(self, limit: Optional[int] = None, alerts_only: bool = False) -> List[Dict[str, Any]]:
        """
        Retorna la lista de eventos registrados, opcionalmente filtrada por alertas.
        """
        with self._lock:
            events_copy = list(self._events)
            
        if alerts_only:
            events_copy = [e for e in events_copy if e["es_alerta"]]
            
        events_copy.reverse()  # Más recientes primero
        
        if limit:
            return events_copy[:limit]
        return events_copy

    def get_stats(self) -> Dict[str, int]:
        """
        Retorna estadísticas rápidas de eventos y alertas.
        """
        with self._lock:
            total = len(self._events)
            alerts = sum(1 for e in self._events if e["es_alerta"])
            critical = sum(1 for e in self._events if e["severidad"] == "CRITICA")
            warning = sum(1 for e in self._events if e["severidad"] == "ADVERTENCIA")
            normal = total - alerts
            return {
                "total": total,
                "alerts": alerts,
                "critical": critical,
                "warning": warning,
                "normal": normal
            }

    def export_to_csv_string(self) -> str:
        """
        Genera el contenido CSV con todos los eventos registrados conforme a RFC 4180.
        """
        output = io.StringIO()
        fieldnames = [
            "id",
            "timestamp",
            "tipo",
            "origen",
            "destino",
            "comando",
            "descripcion",
            "severidad",
            "es_alerta",
            "justificacion_defensiva"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        
        with self._lock:
            for event in self._events:
                writer.writerow(event)
                
        return output.getvalue()

    def clear(self):
        """Limpia el historial de eventos."""
        with self._lock:
            self._events.clear()
            self._counter = 1
