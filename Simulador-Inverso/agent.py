import socket
import json
import time
import sys
from typing import Dict, Any

class SimulatedAgent:
    """
    Agente cliente TCP que implementa la conexión inversa hacia el controlador.
    RF-02: Agente que inicia la conexión hacia el controlador.
    RF-03: Limitar toda comunicación a 127.0.0.1.
    RF-07: Simular apagado sin apagar el equipo.
    RF-08: Simular operación de dispositivo sin modificar hardware.
    RF-09: Enviar y mostrar mensaje de texto.
    RF-14: Rechazar instrucciones desconocidas.
    """
    ALLOWED_COMMANDS = {
        "PING",
        "STATUS",
        "SIMULATE_SHUTDOWN",
        "SIMULATE_DEVICE_ACTION",
        "SEND_TEXT"
    }

    def __init__(self, host: str = "127.0.0.1", port: int = 9000, retry_interval: int = 3):
        if host != "127.0.0.1":
            raise ValueError("RF-03: Toda comunicación debe limitarse estrictamente a 127.0.0.1")
        self.host = host
        self.port = port
        self.retry_interval = retry_interval
        self.is_running = True
        self.device_state = {
            "usb_blocked": False,
            "webcam_status": "IDLE_SIMULATED",
            "mock_disk_quota": "500GB_HEALTHY"
        }

    def connect(self) -> socket.socket:
        """Intenta conectarse al controlador en loopback"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        return s

    def process_instruction(self, raw_json: str) -> Dict[str, Any]:
        """
        Procesa una instrucción recibida.
        Cumple RF-07, RF-08, RF-09 y RF-14 de manera controlada y segura.
        """
        try:
            req = json.loads(raw_json)
        except Exception:
            return {
                "status": "ERROR",
                "is_alert": True,
                "alert_level": "WARNING",
                "message": "Formato de mensaje JSON inválido",
                "data": {}
            }

        cmd = req.get("command", "").upper()
        param = req.get("param", "")

        # RF-14: Rechazo de instrucciones no permitidas
        if cmd not in self.ALLOWED_COMMANDS:
            return {
                "status": "REJECTED",
                "command": cmd,
                "is_alert": True,
                "alert_level": "WARNING",
                "message": f"Instrucción desconocida o rechazada: '{cmd}'. No permitida por política.",
                "data": {"permitted": list(self.ALLOWED_COMMANDS)}
            }

        # RF-05 / CP-03: Consulta de estado (STATUS / PING)
        if cmd in ("STATUS", "PING"):
            return {
                "status": "SUCCESS",
                "command": cmd,
                "is_alert": False,
                "alert_level": "INFO",
                "message": "Agente activo y respondiendo consultas de telemetría.",
                "data": {
                    "agent_uptime_sec": time.time(),
                    "loopback_verified": True,
                    "device_state": self.device_state
                }
            }

        # RF-07 / CP-04: Simulación de apagado (sin apagar el equipo)
        elif cmd == "SIMULATE_SHUTDOWN":
            return {
                "status": "SIMULATED_SHUTDOWN_TRIGGERED",
                "command": cmd,
                "is_alert": True,
                "alert_level": "CRITICAL",
                "message": "ALERTA CRÍTICA: Simulación de instrucción de apagado remoto interceptada. NINGUNA acción física ejecutada.",
                "data": {
                    "action_simulated": "OS_SHUTDOWN_EVENT",
                    "real_effect": "NONE_BLOCKED_BY_SIMULATOR",
                    "timestamp": time.time(),
                    "defense_notes": "En un entorno real, una llamada 'shutdown -s' o syscall similar sería clasificada como T1529 (System Shutdown/Reboot) en MITRE ATT&CK."
                }
            }

        # RF-08 / CP-05: Simulación de operación de dispositivo (sin alterar hardware)
        elif cmd == "SIMULATE_DEVICE_ACTION":
            # Alternar estado simulado de puerto USB o periférico
            new_usb_state = not self.device_state["usb_blocked"]
            self.device_state["usb_blocked"] = new_usb_state
            return {
                "status": "SIMULATED_DEVICE_ACTION_OK",
                "command": cmd,
                "is_alert": True,
                "alert_level": "WARNING",
                "message": f"Simulación de alteración de periférico/dispositivo ejecutada. Estado USB simulado: {'BLOQUEADO' if new_usb_state else 'ACTIVO'}.",
                "data": {
                    "action_simulated": "TOGGLE_USB_PORT_STATE",
                    "real_effect": "NONE_SIMULATION_ONLY",
                    "device_state": self.device_state,
                    "defense_notes": "T1200 (Hardware Additions) o control periférico. La instrucción es emulada en memoria."
                }
            }

        # RF-09 / CP-06: Enviar y mostrar mensaje de texto
        elif cmd == "SEND_TEXT":
            text_received = str(param)
            print(f"\n[AGENTE NOTIFICACIÓN] Mensaje de texto recibido del controlador: '{text_received}'\n")
            return {
                "status": "TEXT_RECEIVED",
                "command": cmd,
                "is_alert": False,
                "alert_level": "INFO",
                "message": f"Mensaje recibido y procesado en el agente: '{text_received}'",
                "data": {
                    "text_payload": text_received,
                    "length": len(text_received),
                    "encoding": "utf-8"
                }
            }

        return {
            "status": "ERROR",
            "is_alert": True,
            "alert_level": "WARNING",
            "message": "Instrucción no procesable.",
            "data": {}
        }

    def run(self):
        """Loop de ejecución principal del agente con reconexión continua"""
        print("="*60)
        print(" [*] AGENTE DE COMUNICACIÓN INVERSA SIMULADO")
        print(" [*] Protocolo: TCP Loopback (127.0.0.1)")
        print(" [*] Modo: Seguro (Todas las acciones destructivas son simuladas)")
        print("="*60)

        while self.is_running:
            try:
                print(f"[+] Intentando conectar al controlador en {self.host}:{self.port}...")
                sock = self.connect()
                print(f"[+] ¡Conexión establecida con éxito hacia el controlador en {self.host}:{self.port}!")
                buffer = ""

                while self.is_running:
                    chunk = sock.recv(1024).decode("utf-8")
                    if not chunk:
                        print("[-] El controlador cerró la conexión TCP.")
                        break
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if not line.strip():
                            continue
                        print(f"[*] Mensaje TCP recibido: {line.strip()}")
                        response = self.process_instruction(line)
                        resp_str = json.dumps(response) + "\n"
                        sock.sendall(resp_str.encode("utf-8"))
                        print(f"[>] Respuesta enviada al controlador: {response['message']}")

                sock.close()
            except ConnectionRefusedError:
                print(f"[-] Controlador no disponible en {self.host}:{self.port} (CP-09). Reintentando en {self.retry_interval}s...")
            except Exception as e:
                print(f"[!] Error de comunicación: {e}. Reintentando en {self.retry_interval}s...")

            time.sleep(self.retry_interval)

if __name__ == "__main__":
    agent = SimulatedAgent()
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n[!] Agente detenido por el usuario.")
        sys.exit(0)
