import socket
import threading
import json
import time
from typing import Optional, Tuple, Dict, Any
from event_manager import EventManager

class ControllerServer:
    """
    Controlador TCP (C2 educacional).
    RF-01: Esperar una conexión TCP local.
    RF-03: Limitar toda comunicación a 127.0.0.1.
    RF-04: Mostrar el estado de la conexión.
    RF-05: Permitir instrucciones predefinidas.
    RF-06: Recibir respuestas y mostrarlas.
    RF-14: Rechazar instrucciones desconocidas.
    """
    ALLOWED_COMMANDS = {
        "PING",
        "STATUS",
        "SIMULATE_SHUTDOWN",
        "SIMULATE_DEVICE_ACTION",
        "SEND_TEXT"
    }

    def __init__(self, host: str = "127.0.0.1", port: int = 9000, event_manager: Optional[EventManager] = None):
        if host != "127.0.0.1":
            raise ValueError("RF-03: Toda comunicación debe limitarse estrictamente a 127.0.0.1")
        self.host = host
        self.port = port
        self.event_manager = event_manager or EventManager()
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.client_address: Optional[Tuple[str, int]] = None
        self.is_running = False
        self.connected = False
        self._lock = threading.Lock()
        self.last_response: Optional[Dict[str, Any]] = None

    def start(self):
        """Inicia el socket servidor y el hilo de escucha"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.is_running = True
        
        self.event_manager.log_event(
            event_type="SERVER_START",
            command="LISTEN",
            source=f"{self.host}:{self.port}",
            destination="N/A",
            category="NORMAL",
            level="INFO",
            details="Controlador iniciado en modo escucha local esperando agente inverso."
        )

        accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        accept_thread.start()

    def _accept_loop(self):
        """Loop receptor de agentes (reverse shell simulator)"""
        while self.is_running:
            try:
                conn, addr = self.server_socket.accept()
                with self._lock:
                    if self.client_socket:
                        try:
                            self.client_socket.close()
                        except Exception:
                            pass
                    self.client_socket = conn
                    self.client_address = addr
                    self.connected = True

                self.event_manager.log_event(
                    event_type="AGENT_CONNECTED",
                    command="CONNECT",
                    source=f"{addr[0]}:{addr[1]}",
                    destination=f"{self.host}:{self.port}",
                    category="NORMAL",
                    level="INFO",
                    details=f"Conexión inversa establecida exitosamente desde el agente en {addr[0]}:{addr[1]}."
                )
            except Exception:
                if not self.is_running:
                    break

    def send_command(self, command: str, param: str = "") -> Dict[str, Any]:
        """
        Envía una instrucción al agente y espera su respuesta sincronizada.
        RF-05, RF-06, RF-14
        """
        cmd_upper = command.strip().upper()

        if cmd_upper not in self.ALLOWED_COMMANDS:
            # RF-14: Rechazar instrucciones desconocidas
            event = self.event_manager.log_event(
                event_type="COMMAND_REJECTED",
                command=command,
                source=f"{self.host}:{self.port}",
                destination="N/A",
                category="ALERTA",
                level="WARNING",
                details=f"Instrucción desconocida o no autorizada '{command}' rechazada por el controlador.",
                response="ERROR: Comando no permitido por la política de seguridad."
            )
            return {
                "success": False,
                "command": command,
                "error": "Instrucción no autorizada o fuera del conjunto permitido (RF-14).",
                "details": event["details"]
            }

        with self._lock:
            if not self.connected or not self.client_socket:
                self.event_manager.log_event(
                    event_type="DISPATCH_FAILED",
                    command=cmd_upper,
                    source=f"{self.host}:{self.port}",
                    destination="N/A",
                    category="ALERTA",
                    level="WARNING",
                    details=f"Fallo al enviar '{cmd_upper}': No hay ningún agente conectado (CP-09).",
                    response="ERROR: Agente offline."
                )
                return {
                    "success": False,
                    "command": cmd_upper,
                    "error": "No hay agente conectado actualmente.",
                    "details": "Agente no disponible."
                }

            # Preparar payload JSON sobre TCP
            payload = json.dumps({"command": cmd_upper, "param": param}) + "\n"
            try:
                self.client_socket.sendall(payload.encode("utf-8"))
            except Exception as e:
                self._handle_disconnect()
                return {"success": False, "error": f"Error al transmitir socket: {str(e)}"}

            # Esperar respuesta directa
            try:
                self.client_socket.settimeout(5.0)
                raw_response = b""
                while not raw_response.endswith(b"\n"):
                    chunk = self.client_socket.recv(1024)
                    if not chunk:
                        self._handle_disconnect()
                        return {"success": False, "error": "El agente cerró la conexión TCP."}
                    raw_response += chunk

                resp_data = json.loads(raw_response.decode("utf-8").strip())
                self.last_response = resp_data

                # Clasificar evento para auditoría
                category = "ALERTA" if resp_data.get("is_alert", False) else "NORMAL"
                level = resp_data.get("alert_level", "INFO")
                
                self.event_manager.log_event(
                    event_type=f"EXEC_{cmd_upper}",
                    command=cmd_upper,
                    source=f"{self.host}:{self.port}",
                    destination=f"{self.client_address[0]}:{self.client_address[1]}" if self.client_address else "AGENTE",
                    category=category,
                    level=level,
                    details=resp_data.get("message", "Instrucción ejecutada."),
                    response=json.dumps(resp_data.get("data", {}), ensure_ascii=False)
                )

                return {
                    "success": True,
                    "command": cmd_upper,
                    "agent_response": resp_data
                }

            except socket.timeout:
                return {"success": False, "error": "Tiempo de espera (timeout) agotado esperando al agente."}
            except Exception as e:
                self._handle_disconnect()
                return {"success": False, "error": f"Error recibiendo respuesta: {str(e)}"}

    def _handle_disconnect(self):
        """Registra desconexión de forma segura"""
        addr = self.client_address
        self.client_socket = None
        self.client_address = None
        self.connected = False
        if addr:
            self.event_manager.log_event(
                event_type="AGENT_DISCONNECTED",
                command="DISCONNECT",
                source=f"{addr[0]}:{addr[1]}",
                destination=f"{self.host}:{self.port}",
                category="ALERTA",
                level="WARNING",
                details=f"Agente desconectado de {addr[0]}:{addr[1]}."
            )

    def get_status(self) -> Dict[str, Any]:
        """RF-04: Mostrar el estado de la conexión"""
        with self._lock:
            # Probar si el socket sigue vivo si está marcado como conectado
            if self.connected and self.client_socket:
                try:
                    # Enviar 0 bytes o comprobar estado no bloqueante
                    self.client_socket.settimeout(0.0)
                    peek = self.client_socket.recv(1, socket.MSG_PEEK)
                    if peek == b"":
                        # Socket cerrado remotamente
                        self._handle_disconnect()
                except BlockingIOError:
                    pass
                except Exception:
                    self._handle_disconnect()
                finally:
                    if self.client_socket:
                        self.client_socket.settimeout(None)

            return {
                "server_running": self.is_running,
                "server_host": self.host,
                "server_port": self.port,
                "agent_connected": self.connected,
                "agent_address": f"{self.client_address[0]}:{self.client_address[1]}" if self.client_address else None,
                "last_response": self.last_response
            }

    def stop(self):
        """Detiene el servidor controlador"""
        self.is_running = False
        with self._lock:
            if self.client_socket:
                try:
                    self.client_socket.close()
                except Exception:
                    pass
                self.client_socket = None
            if self.server_socket:
                try:
                    self.server_socket.close()
                except Exception:
                    pass
                self.server_socket = None
            self.connected = False
