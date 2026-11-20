import time
import threading
from controller import ControllerServer
from agent import SimulatedAgent
from event_manager import EventManager

def run_lab_session():
    print("[+] Iniciando sesión de laboratorio para generación de evidencias reales...")
    em = EventManager()
    server = ControllerServer(host="127.0.0.1", port=9000, event_manager=em)
    server.start()
    
    agent = SimulatedAgent(host="127.0.0.1", port=9000)
    
    # Iniciar agente en un hilo
    t_agent = threading.Thread(target=agent.run, daemon=True)
    t_agent.start()
    
    time.sleep(1.0)
    
    # 1. STATUS (RF-05 / CP-03)
    print("-> Enviando STATUS...")
    server.send_command("STATUS")
    time.sleep(0.5)
    
    # 2. SEND_TEXT (RF-09 / CP-06)
    print("-> Enviando SEND_TEXT...")
    server.send_command("SEND_TEXT", "Monitoreo defensivo: enlace activo en loopback.")
    time.sleep(0.5)
    
    # 3. SIMULATE_DEVICE_ACTION (RF-08 / CP-05)
    print("-> Enviando SIMULATE_DEVICE_ACTION...")
    server.send_command("SIMULATE_DEVICE_ACTION")
    time.sleep(0.5)
    
    # 4. SIMULATE_SHUTDOWN (RF-07 / CP-04)
    print("-> Enviando SIMULATE_SHUTDOWN...")
    server.send_command("SIMULATE_SHUTDOWN")
    time.sleep(0.5)
    
    # 5. Comando no autorizado (RF-14 / CP-07)
    print("-> Probando comando no autorizado...")
    server.send_command("SHELL_EXEC_POWERSHELL", "Get-Process")
    time.sleep(0.5)
    
    # 6. Intentar comando offline (CP-09)
    print("-> Deteniendo agente y simulando envío offline...")
    agent.is_running = False
    time.sleep(1.0)
    server.send_command("STATUS")
    
    # Exportar CSV real
    csv_data = em.export_csv()
    with open("c:/Users/Fernando/Documents/code/actividad-cyberseguridad/Simulador-Inverso/evidencias_eventos.csv", "w", encoding="utf-8") as f:
        f.write(csv_data)
    
    server.stop()
    print("[+] Evidencias generadas exitosamente en 'Simulador-Inverso/evidencias_eventos.csv'.")

if __name__ == "__main__":
    run_lab_session()
