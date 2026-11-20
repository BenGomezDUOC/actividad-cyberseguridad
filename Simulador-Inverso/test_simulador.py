import pytest
import time
import json
import threading
from controller import ControllerServer
from agent import SimulatedAgent
from event_manager import EventManager

@pytest.fixture
def test_setup():
    """Configura un entorno aislado para pruebas unitarias e integración"""
    em = EventManager()
    server = ControllerServer(host="127.0.0.1", port=9005, event_manager=em)
    server.start()
    agent = SimulatedAgent(host="127.0.0.1", port=9005)
    
    yield {"server": server, "agent": agent, "em": em}
    
    server.stop()
    agent.is_running = False

def test_cp09_failed_connection_handling():
    """CP-09: El sistema maneja un intento de conexión fallido adecuadamente"""
    em = EventManager()
    # Conectarse a un puerto sin escuchar
    agent = SimulatedAgent(host="127.0.0.1", port=9998)
    with pytest.raises(ConnectionRefusedError):
        agent.connect()

def test_cp01_agent_connects_local(test_setup):
    """CP-01: El agente establece la conexión local"""
    server = test_setup["server"]
    agent = test_setup["agent"]
    
    sock = agent.connect()
    time.sleep(0.5)
    
    status = server.get_status()
    assert status["agent_connected"] is True
    assert "127.0.0.1" in status["agent_address"]
    sock.close()

def test_cp02_panel_status_reflection(test_setup):
    """CP-02: El panel/controlador refleja correctamente el estado"""
    server = test_setup["server"]
    agent = test_setup["agent"]
    
    # Inicialmente desconectado
    assert server.get_status()["agent_connected"] is False
    
    sock = agent.connect()
    time.sleep(0.5)
    assert server.get_status()["agent_connected"] is True
    
    sock.close()
    time.sleep(1.0)
    assert server.get_status()["agent_connected"] is False

def test_cp03_cp04_cp05_cp06_cp07_instructions(test_setup):
    """
    CP-03: Consulta de estado recibe respuesta
    CP-04: Simulación de apagado genera alerta sin efectos
    CP-05: Simulación de dispositivo genera evento
    CP-06: Mensaje de texto llega al agente
    CP-07: Instrucción desconocida rechazada
    """
    server = test_setup["server"]
    agent = test_setup["agent"]
    em = test_setup["em"]
    
    # Conectar agente con hilo para responder
    sock = agent.connect()
    
    def agent_listener():
        buffer = ""
        while agent.is_running:
            try:
                data = sock.recv(1024).decode("utf-8")
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        res = agent.process_instruction(line)
                        sock.sendall((json.dumps(res) + "\n").encode("utf-8"))
            except Exception:
                break

    t = threading.Thread(target=agent_listener, daemon=True)
    t.start()
    time.sleep(0.5)

    # CP-03: STATUS
    res_status = server.send_command("STATUS")
    assert res_status["success"] is True
    assert res_status["agent_response"]["status"] == "SUCCESS"
    assert res_status["agent_response"]["is_alert"] is False

    # CP-04: SIMULATE_SHUTDOWN
    res_shut = server.send_command("SIMULATE_SHUTDOWN")
    assert res_shut["success"] is True
    assert res_shut["agent_response"]["alert_level"] == "CRITICAL"
    assert res_shut["agent_response"]["data"]["real_effect"] == "NONE_BLOCKED_BY_SIMULATOR"

    # CP-05: SIMULATE_DEVICE_ACTION
    res_dev = server.send_command("SIMULATE_DEVICE_ACTION")
    assert res_dev["success"] is True
    assert res_dev["agent_response"]["data"]["real_effect"] == "NONE_SIMULATION_ONLY"

    # CP-06: SEND_TEXT
    res_text = server.send_command("SEND_TEXT", "Mensaje de auditoría de red")
    assert res_text["success"] is True
    assert res_text["agent_response"]["data"]["text_payload"] == "Mensaje de auditoría de red"

    # CP-07: Instrucción desconocida rechazada
    res_inv = server.send_command("MALICIOUS_CMD")
    assert res_inv["success"] is False
    assert "no permitida" in res_inv["error"].lower() or "rechazada" in res_inv["details"].lower()

    # CP-08: Exportación CSV
    csv_out = em.export_csv()
    assert "COMMAND_REJECTED" in csv_out
    assert "SIMULATE_SHUTDOWN" in csv_out
    assert "timestamp,event_type" in csv_out

    sock.close()
