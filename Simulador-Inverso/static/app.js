// Lógica de interacción en tiempo real para el panel C2
let isPolling = true;

document.addEventListener("DOMContentLoaded", () => {
    updateStatus();
    updateEvents();
    // Sondeo periódico cada 2 segundos (RF-12)
    setInterval(() => {
        if (isPolling) {
            updateStatus();
            updateEvents();
        }
    }, 2000);
});

async function updateStatus() {
    try {
        const response = await fetch("/api/status");
        if (!response.ok) return;
        const data = await response.json();
        
        const status = data.status;
        const stats = data.stats;

        // Actualizar píldora de conexión (RF-04)
        const pill = document.getElementById("connection-pill");
        const pillText = document.getElementById("connection-text");
        const metaAgent = document.getElementById("meta-agent");
        const metaServer = document.getElementById("meta-server");

        if (status.agent_connected) {
            pill.className = "status-pill online";
            pillText.textContent = `Agente Conectado (${status.agent_address})`;
            metaAgent.textContent = status.agent_address;
            metaAgent.style.color = "#34d399";
        } else {
            pill.className = "status-pill offline";
            pillText.textContent = "Agente Desconectado";
            metaAgent.textContent = "Esperando conexión inversa...";
            metaAgent.style.color = "#f87171";
        }

        metaServer.textContent = `${status.server_host}:${status.server_port}`;

        // Métricas
        document.getElementById("stat-total").textContent = stats.total;
        document.getElementById("stat-normal").textContent = stats.normal;
        document.getElementById("stat-alerts").textContent = stats.alerts;
        document.getElementById("stat-critical").textContent = stats.critical;

    } catch (err) {
        console.error("Error al consultar estado:", err);
    }
}

async function updateEvents() {
    try {
        const response = await fetch("/api/events");
        if (!response.ok) return;
        const data = await response.json();
        const events = data.events;

        const tbody = document.getElementById("events-table-body");
        if (!events || events.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center" style="padding: 24px; color: #94a3b8;">No hay eventos registrados aún.</td></tr>`;
            return;
        }

        tbody.innerHTML = events.map(evt => {
            const catBadge = evt.category === "ALERTA" 
                ? `<span class="badge-tag badge-alerta">ALERTA</span>` 
                : `<span class="badge-tag badge-normal">NORMAL</span>`;
            
            let lvlClass = "badge-info";
            if (evt.level === "WARNING") lvlClass = "badge-warning";
            if (evt.level === "CRITICAL") lvlClass = "badge-critical";

            return `
                <tr>
                    <td><code>#${evt.id}</code></td>
                    <td><small>${evt.timestamp}</small></td>
                    <td><strong>${evt.event_type}</strong></td>
                    <td><code>${evt.command}</code></td>
                    <td><code>${evt.source}</code></td>
                    <td><code>${evt.destination}</code></td>
                    <td>${catBadge}</td>
                    <td><span class="badge-tag ${lvlClass}">${evt.level}</span></td>
                    <td>${escapeHtml(evt.details)}</td>
                </tr>
            `;
        }).join("");

    } catch (err) {
        console.error("Error al consultar eventos:", err);
    }
}

async function sendCommand(command, param = "") {
    try {
        const responseContent = document.getElementById("response-content");
        const responseTimestamp = document.getElementById("response-timestamp");
        
        responseContent.textContent = `Enviando instrucción '${command}' por socket TCP...`;
        responseTimestamp.textContent = new Date().toLocaleTimeString();

        const res = await fetch("/api/send-command", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: command, param: param })
        });

        const data = await res.json();
        responseContent.textContent = JSON.stringify(data, null, 2);
        responseTimestamp.textContent = new Date().toLocaleTimeString();

        // Actualizar tabla y estadísticas inmediatamente
        updateStatus();
        updateEvents();

    } catch (err) {
        document.getElementById("response-content").textContent = `Error de conexión: ${err.message}`;
    }
}

function sendTextMessage() {
    const input = document.getElementById("text-param");
    const msg = input.value.trim();
    if (!msg) {
        alert("Por favor ingrese un mensaje de texto.");
        return;
    }
    sendCommand("SEND_TEXT", msg);
}

function sendCustomInvalidCommand() {
    const cmd = prompt("Ingrese un comando para probar el rechazo defensivo (RF-14 / CP-07):", "SHELL_EXEC_POWERSHELL");
    if (cmd) {
        sendCommand(cmd, "unauthorized_payload");
    }
}

async function clearLogs() {
    if (!confirm("¿Está seguro de limpiar la bitácora de eventos del laboratorio?")) return;
    try {
        await fetch("/api/clear-events", { method: "POST" });
        updateStatus();
        updateEvents();
    } catch (err) {
        alert("Error al limpiar bitácora");
    }
}

function escapeHtml(string) {
    if (!string) return "";
    return String(string)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
