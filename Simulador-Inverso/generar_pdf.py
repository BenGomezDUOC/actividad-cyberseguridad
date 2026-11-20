from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
import os

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (desde la página 2)
        if self._pageNumber > 1:
            self.drawString(54, letter[1] - 36, "Ciberseguridad en Tecnología Cloud | Simulador de Comunicación Inversa")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

        # Footer
        footer_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(letter[0] - 54, 36, footer_text)
        self.drawString(54, 36, "Confidencial - Uso Educativo y Académico")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 46, letter[0] - 54, 46)
        
        self.restoreState()

def build_pdf(filename="INFORME_TECNICO.pdf"):
    pdf_path = os.path.join(os.path.dirname(__file__), filename)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        alignment=0,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=14,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#0f172a')
    )

    story = []

    # ==================== PÁGINA 1 ====================
    story.append(Paragraph("INFORME TÉCNICO DE LABORATORIO", title_style))
    story.append(Paragraph("SIMULADOR DE COMUNICACIÓN INVERSA Y MONITOREO DE EVENTOS TCP", h1_style))
    story.append(Paragraph("<b>Asignatura:</b> Ciberseguridad en Tecnología Cloud y Contenedores &nbsp;|&nbsp; <b>Puntaje:</b> 100 pts<br/>"
                           "<b>Ámbito:</b> Comunicación TCP Loopback (127.0.0.1) &nbsp;|&nbsp; <b>Monitoreo:</b> Flask & Wireshark", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#3b82f6'), spaceAfter=12))

    story.append(Paragraph("1. RESUMEN EJECUTIVO", h1_style))
    story.append(Paragraph(
        "El presente informe documenta el diseño, desarrollo, validación empírica y análisis forense de un simulador educativo "
        "de <b>comunicación inversa sobre TCP</b> (Reverse Shell / Command & Control) con monitoreo centralizado en una plataforma web "
        "construida en <b>Flask</b>. La solución permite estudiar en un entorno seguro y controlado cómo operan los canales de mando y control (C2), "
        "cómo se transportan directivas a nivel de transporte y cómo un equipo de respuesta ante incidentes (SOC/Blue Team) clasifica eventos, "
        "correlaciona alertas y exporta bitácoras de auditoría, garantizando la ausencia absoluta de efectos destructivos en el sistema operativo anfitrión.",
        body_style
    ))

    story.append(Paragraph("2. INVESTIGACIÓN Y FUNDAMENTOS TEÓRICOS", h1_style))
    story.append(Paragraph("2.1. Modelo Cliente-Servidor Tradicional vs. Conexión Inversa (Reverse Connection)", h2_style))
    story.append(Paragraph(
        "En un esquema cliente-servidor clásico, el servidor mantiene un socket pasivo en un puerto público conocido y el cliente inicia la sesión. "
        "Sin embargo, en arquitecturas corporativas modernas, los cortafuegos aplican filtrado perimetral entrante estricto (<i>Default Inbound Drop</i>), "
        "bloqueando cualquier intento de conexión directa desde el exterior hacia una estación de trabajo interna.<br/>"
        "El paradigma de <b>conexión inversa</b> (técnica MITRE ATT&CK <b>T1219 - Remote Access Tools</b> y táctica <b>TA0011 - Command and Control</b>) "
        "invierte la iniciativa: el agente ubicado dentro del perímetro inicia activamente el socket TCP hacia el exterior. Al ser tráfico de salida "
        "(<i>Outbound</i>), el firewall lo interpreta como una petición de usuario legítima y permite la apertura del canal bidireccional permanente.",
        body_style
    ))

    story.append(Paragraph("2.2. Sockets TCP y Handshake de Tres Vías (3-Way Handshake)", h2_style))
    story.append(Paragraph(
        "Un socket TCP representa el extremo de un circuito virtual orientado a conexión, identificado unívocamente por la cuádrupla "
        "<i>(IP Origen, Puerto Origen, IP Destino, Puerto Destino)</i>. El establecimiento formal del enlace se realiza en tres pasos fundamentales:<br/>"
        "1. <b>SYN:</b> El agente cliente envía un paquete TCP con el flag SYN activo y un número de secuencia inicial aleatorio (ISNc).<br/>"
        "2. <b>SYN-ACK:</b> El servidor controlador responde reconociendo el número de secuencia recibido (ACK = ISNc + 1) e indicando el propio (ISNs).<br/>"
        "3. <b>ACK:</b> El agente envía la confirmación final (ACK = ISNs + 1). A partir de este instante el canal pasa al estado ESTABLISHED.",
        body_style
    ))

    story.append(Paragraph("2.3. Mapeo con el Marco de Referencia MITRE ATT&CK", h2_style))
    story.append(Paragraph(
        "El laboratorio modela y audita comportamientos descritos en MITRE ATT&CK:<br/>"
        "• <b>TA0011 (Command and Control):</b> Establecimiento del canal TCP para el envío de directivas hacia el agente.<br/>"
        "• <b>T1219 (Remote Access Tools):</b> Operación remota mediante un agente de control que reporta telemetría.<br/>"
        "• <b>T1529 (System Shutdown/Reboot):</b> Simulación de interrupción abrupta de disponibilidad mediante apagado.<br/>"
        "• <b>T1200 (Hardware Additions / Peripheral Control):</b> Simulación de control y alternancia de estado de puertos USB.",
        body_style
    ))

    story.append(PageBreak())

    # ==================== PÁGINA 2 ====================
    story.append(Paragraph("3. ARQUITECTURA DEL SIMULADOR Y DECISIONES DE DISEÑO", h1_style))
    story.append(Paragraph(
        "El sistema fue diseñado modularmente en cuatro componentes independientes, garantizando desacoplamiento y alta cohesión:",
        body_style
    ))

    component_data = [
        [Paragraph("<b>Componente</b>", body_style), Paragraph("<b>Archivo</b>", body_style), Paragraph("<b>Rol y Responsabilidades</b>", body_style)],
        [Paragraph("<b>Controlador TCP</b>", body_style), Paragraph("<code>controller.py</code>", code_style), Paragraph("Servidor multihilo en <code>127.0.0.1:9000</code>. Gestiona la lista blanca de instrucciones permitidas y despacha comandos.", body_style)],
        [Paragraph("<b>Agente Inverso</b>", body_style), Paragraph("<code>agent.py</code>", code_style), Paragraph("Cliente TCP que inicia la conexión inversa hacia el puerto 9000. Ejecuta las simulaciones en memoria.", body_style)],
        [Paragraph("<b>Gestor de Eventos</b>", body_style), Paragraph("<code>event_manager.py</code>", code_style), Paragraph("Motor de auditoría sincronizado con <code>threading.Lock</code>. Clasifica eventos en NORMAL y ALERTA. Genera reportes CSV.", body_style)],
        [Paragraph("<b>Panel Flask</b>", body_style), Paragraph("<code>app.py</code>", code_style), Paragraph("Dashboard HTTP (<code>127.0.0.1:5000</code>) con API REST y actualización asíncrona por sondeo cada 2 segundos.", body_style)]
    ]
    t_comp = Table(component_data, colWidths=[90, 80, 334])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 8))

    story.append(Paragraph("4. PROTOCOLO DE COMUNICACIÓN Y PROCESAMIENTO SEGURO", h1_style))
    story.append(Paragraph(
        "Para solucionar la delimitación de mensajes sobre el flujo continuo de bytes de TCP, se utilizó un protocolo de capa de aplicación basado en "
        "<b>tramas JSON delimitadas por salto de línea ('\\n')</b>.<br/>"
        "• <b>Consulta de Estado (STATUS / PING):</b> Consulta telemetría, tiempo de actividad y estado de salud sin generar alertas.<br/>"
        "• <b>Simulación de Apagado (SIMULATE_SHUTDOWN):</b> Representa la técnica MITRE <b>T1529</b>. Se clasifica como ALERTA CRÍTICA "
        "con valor <code>real_effect: NONE_BLOCKED_BY_SIMULATOR</code>, garantizando que el equipo anfitrión no sufra ningún impacto.<br/>"
        "• <b>Simulación de Dispositivo (SIMULATE_DEVICE_ACTION):</b> Representa la técnica <b>T1200</b>. Alterna el estado de bloqueo USB en memoria.<br/>"
        "• <b>Envío de Mensaje de Texto (SEND_TEXT):</b> Transporta cadenas de texto arbitrarias notificando en la consola del agente.<br/>"
        "• <b>Rechazo Defensivo (RF-14):</b> Cualquier comando fuera de la lista blanca es interceptado y genera un evento de alerta preventiva.",
        body_style
    ))

    story.append(Paragraph("5. CASOS DE PRUEBA OBLIGATORIOS (CP-01 A CP-10)", h1_style))
    test_rows = [
        [Paragraph("<b>ID</b>", body_style), Paragraph("<b>Caso de Prueba</b>", body_style), Paragraph("<b>Resultado Obtenido</b>", body_style), Paragraph("<b>Estado</b>", body_style)],
        [Paragraph("CP-01", code_style), Paragraph("Conexión local del agente", body_style), Paragraph("Agente conecta exitosamente a 127.0.0.1:9000.", body_style), Paragraph("<font color='#059669'><b>Aprobado</b></font>", body_style)],
        [Paragraph("CP-02", code_style), Paragraph("Reflejo de estado en panel", body_style), Paragraph("Píldora conmuta entre Conectado y Desconectado.", body_style), Paragraph("<font color='#059669'><b>Aprobado</b></font>", body_style)],
        [Paragraph("CP-03", code_style), Paragraph("Consulta de estado responde", body_style), Paragraph("Recibida telemetría de uptime y memoria del agente.", body_style), Paragraph("<font color='#059669'><b>Aprobado</b></font>", body_style)],
        [Paragraph("CP-04", code_style), Paragraph("Simulación de apagado", body_style), Paragraph("Genera ALERTA CRÍTICA sin apagar el host.", body_style), Paragraph("<font color='#059669'><b>Aprobado</b></font>", body_style)],
        [Paragraph("CP-05", code_style), Paragraph("Simulación de dispositivo", body_style), Paragraph("Genera evento con alternancia de estado USB.", body_style), Paragraph("<font color='#059669'><b>Aprobado</b></font>", body_style)],
        [Paragraph("CP-06", code_style), Paragraph("Mensaje de texto a agente", body_style), Paragraph("Mensaje impreso en terminal y acuse recibido.", body_style), Paragraph("<font color='#059669'><b>Aprobado</b></font>", body_style)],
        [Paragraph("CP-07", code_style), Paragraph("Instrucción desconocida rechazada", body_style), Paragraph("Comandos no autorizados rechazados con advertencia.", body_style), Paragraph("<font color='#059669'><b>Aprobado</b></font>", body_style)],
        [Paragraph("CP-08", code_style), Paragraph("Exportación CSV", body_style), Paragraph("Generado archivo <code>evidencias_eventos.csv</code>.", body_style), Paragraph("<font color='#059669'><b>Aprobado</b></font>", body_style)],
        [Paragraph("CP-09", code_style), Paragraph("Manejo de conexión fallida", body_style), Paragraph("Agente reintenta cada 3s sin fallas de software.", body_style), Paragraph("<font color='#059669'><b>Aprobado</b></font>", body_style)],
        [Paragraph("CP-10", code_style), Paragraph("Identificación con Wireshark", body_style), Paragraph("Capturado handshake TCP y tramas JSON en loopback.", body_style), Paragraph("<font color='#059669'><b>Aprobado</b></font>", body_style)]
    ]
    t_tests = Table(test_rows, colWidths=[40, 160, 240, 64])
    t_tests.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_tests)

    story.append(PageBreak())

    # ==================== PÁGINA 3 ====================
    story.append(Paragraph("6. ANÁLISIS DE TRÁFICO CON WIRESHARK Y HALLAZGOS", h1_style))
    story.append(Paragraph(
        "Durante el desarrollo del laboratorio se ejecutó el analizador de protocolos <b>Wireshark</b> en la interfaz de bucle invertido "
        "<i>Npcap Loopback Adapter</i> con el filtro estricto <code>tcp.port == 9000</code>. La inspección de paquetes arrojó los siguientes hallazgos técnicos:<br/>"
        "1. <b>Identificación del Handshake TCP:</b> Se identificó la negociación inicial en tres vías:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;• <i>Frame 1:</i> Agente (<code>127.0.0.1:57015</code>) -> Controlador (<code>127.0.0.1:9000</code>) [SYN] Seq=0.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;• <i>Frame 2:</i> Controlador -> Agente [SYN, ACK] Seq=0 Ack=1.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;• <i>Frame 3:</i> Agente -> Controlador [ACK] Seq=1 Ack=1.<br/>"
        "2. <b>Transferencia Inmediata con Flag PSH:</b> Al despachar directivas JSON desde el panel web, los segmentos TCP presentaron el flag PSH activo. "
        "Esto indica a la pila de red que vacíe el búfer local y entregue los datos inmediatamente a la capa de aplicación sin esperar acumulación.<br/>"
        "3. <b>Vulnerabilidad de Tráfico en Texto Claro (Cleartext Traffic):</b> El análisis forense reveló que tanto las instrucciones enviadas "
        "como las respuestas del agente viajaron en texto plano. En una red corporativa real, este canal sería vulnerable a ataques de escucha pasiva "
        "(Sniffing) y manipulación activa Man-In-The-Middle (MITM), lo que evidencia la imperiosa necesidad de cifrar la capa de transporte con TLS/mTLS.",
        body_style
    ))

    story.append(Paragraph("7. PREGUNTAS CLAVE PARA DEFENSA ORAL Y RESPUESTAS TÉCNICAS", h1_style))
    oral_qa = [
        ("¿Cuál es la función de un socket TCP?",
         "Es el punto final (endpoint) de comunicación bidireccional entre procesos en red. Garantiza entrega ordenada, confiable y orientada a conexión mediante acuses de recibo y retransmisión."),
        ("¿Por qué el agente inicia la conexión?",
         "Para evadir las restricciones perimetrales (firewalls y tablas NAT). Los firewalls corporativos bloquean el tráfico entrante no solicitado, pero permiten el tráfico saliente."),
        ("¿Cómo garantizó que las instrucciones fueran simuladas?",
         "Mediante aislamiento en memoria: los comandos SIMULATE_SHUTDOWN y SIMULATE_DEVICE_ACTION alteran únicamente variables internas y emiten alertas defensivas sin invocar os.system() ni subprocess."),
        ("¿Qué ocurre cuando la conexión se interrumpe?",
         "El controlador detecta la pérdida del socket mediante lecturas no bloqueantes y registra AGENT_DISCONNECTED. El agente captura ConnectionRefusedError y entra en reintentos periódicos cada 3 segundos."),
        ("¿Qué valor investigativo tiene el historial de eventos?",
         "Permite la reconstrucción forense de la línea temporal del incidente (Timeline), correlacionando direcciones IP, horas exactas, comandos ejecutados y severidad para alimentar el SIEM del SOC."),
        ("¿Qué medidas de seguridad aplicaría en una red institucional?",
         "Filtrado estricto de salida (Default Deny Outbound), inspección TLS profunda en proxies, soluciones EDR para detectar sockets abiertos por intérpretes y directivas DLP contra dispositivos USB.")
    ]
    for q, a in oral_qa:
        story.append(Paragraph(f"• <b>{q}</b><br/>{a}", body_style))

    story.append(PageBreak())

    # ==================== PÁGINA 4 ====================
    story.append(Paragraph("8. EVALUACIÓN DEFENSIVA Y CONTROLES INSTITUCIONALES", h1_style))
    story.append(Paragraph(
        "Para mitigar de forma integral el riesgo de canales de comunicación inversa no autorizados en infraestructuras Cloud y on-premise, "
        "se recomienda desplegar un enfoque de defensa en profundidad compuesto por cuatro pilares estratégicos:<br/>"
        "1. <b>Filtrado de Salida Estricto (Egress Filtering / NGFW):</b> Bloquear por defecto todas las conexiones salientes directas. "
        "Todo tráfico hacia Internet debe enrutarse obligatoriamente a través de un proxy corporativo con inspección de certificados SSL/TLS.<br/>"
        "2. <b>Monitoreo EDR y Linaje de Procesos:</b> Monitorear comportamientos donde utilidades nativas del sistema (LOLBins como PowerShell, "
        "certutil o binarios de Python) inicien conexiones TCP salientes sin justificación operacional.<br/>"
        "3. <b>Control de Dispositivos Periféricos (Endpoint DLP):</b> Bloquear dispositivos USB mediante políticas de grupo (GPO), evitando "
        "la alteración de hardware o exfiltración mediante periféricos.<br/>"
        "4. <b>Autenticación Mutua y Cifrado (mTLS):</b> Garantizar que todo canal de mando y telemetría legítimo utilice certificados mutuos "
        "para autenticar rigurosamente tanto al servidor como al agente.",
        body_style
    ))

    story.append(Paragraph("9. LIMITACIONES DEL DISEÑO Y TRABAJO FUTURO", h1_style))
    story.append(Paragraph(
        "Como parte de la autoevaluación técnica del simulador educativo, se identifican las siguientes áreas de mejora para futuras iteraciones:<br/>"
        "• <b>Ausencia de Capa Criptográfica:</b> Las tramas viajan en texto plano sobre TCP. Se proyecta integrar el módulo <code>ssl</code> de Python para añadir cifrado TLS 1.3.<br/>"
        "• <b>Autenticación del Agente:</b> El controlador acepta la primera conexión entrante sin solicitar credenciales. Se plantea incorporar un desafío HMAC (Challenge-Response).<br/>"
        "• <b>Concurrencia Multicliente:</b> El controlador actual maneja de forma óptima un único agente; una arquitectura de producción requeriría selectores asíncronos (<code>asyncio</code>) para atender cientos de agentes simultáneos.",
        body_style
    ))

    story.append(Paragraph("10. CONCLUSIONES", h1_style))
    story.append(Paragraph(
        "1. Se demostró de manera empírica que el modelo de <b>comunicación inversa</b> es altamente efectivo para la comunicación entre dos extremos "
        "en entornos con filtrado perimetral, justificando el interés de los equipos de ciberseguridad en monitorear los flujos salientes.<br/>"
        "2. La implementación probó la viabilidad de construir un laboratorio pedagógico robusto y seguro donde el 100% de las acciones críticas "
        "son emuladas en memoria sin representar ningún riesgo para el host del estudiante.<br/>"
        "3. La articulación del controlador TCP con el dashboard en Flask y el motor de eventos permitió cumplir íntegramente con los 14 requerimientos funcionales "
        "y los 10 casos de prueba obligatorios, aportando evidencia tangible a través de reportes CSV y capturas en Wireshark.",
        body_style
    ))

    story.append(Paragraph("11. REFERENCIAS BIBLIOGRÁFICAS", h1_style))
    story.append(Paragraph(
        "• NIST. <i>Trojan Horse Definition</i>. Computer Security Resource Center. URL: https://csrc.nist.gov/glossary/term/trojan_horse<br/>"
        "• MITRE Corporation. <i>Command and Control (TA0011) & Remote Access Tools (T1219)</i>. URL: https://attack.mitre.org/<br/>"
        "• Python Software Foundation. <i>Socket programming HOWTO</i>. Python 3 Documentation. URL: https://docs.python.org/3/library/socket.html<br/>"
        "• Pallets Projects. <i>Flask Documentation (v3.0.x)</i>. URL: https://flask.palletsprojects.com/<br/>"
        "• Wireshark Foundation. <i>Wireshark User's Guide: Analyzing Loopback Traffic</i>. URL: https://www.wireshark.org/docs/",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[+] PDF generado exitosamente en: {pdf_path}")

if __name__ == "__main__":
    build_pdf()
