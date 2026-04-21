import smtplib
import os
from email.message import EmailMessage
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

def enviar_reporte():
    remitente = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    destinatarios = ["joseph.cervantes@iplusd.cl"]

    if not remitente or not password:
        logger.error("Faltan EMAIL_USER o EMAIL_PASS en las variables de entorno.")
        return

    fecha = datetime.now().strftime("%d/%m/%Y")

    msg = EmailMessage()
    msg['Subject'] = f' Auditoría DT Completada - {fecha}'
    msg['From'] = remitente
    msg['To'] = ", ".join(destinatarios)
    msg.set_content(
        f"Hola,\n\n"
        f"Se adjunta el reporte consolidado de auditoría generado hoy {fecha}.\n\n"
        f"Saludos,\n"
        f"Bot de Auditoría Automática."
    )

    archivo_zip = None
    logger.info("Buscando el archivo ZIP...")
    for ruta in [".", "reports"]:
        if os.path.exists(ruta):
            for f in os.listdir(ruta):
                nombre_f = f.lower()
                if nombre_f.endswith(".zip") and ("paquete" in nombre_f or "auditoria" in nombre_f):
                    archivo_zip = os.path.join(ruta, f)
                    break
        if archivo_zip:
            break

    if archivo_zip:
        logger.info(f"Archivo detectado: {archivo_zip}")
        try:
            with open(archivo_zip, 'rb') as f:
                msg.add_attachment(
                    f.read(),
                    maintype='application',
                    subtype='zip',
                    filename=os.path.basename(archivo_zip)
                )

            logger.info("Conectando a smtp.gmail.com...")
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                logger.info(f"Intentando login con {remitente}...")
                server.login(remitente, password)
                server.send_message(msg)

            logger.info("Correo enviado correctamente.")

        except Exception as e:
            logger.error(f"Error al enviar el correo: {e}")
            logger.error("Tip: Asegúrate de que EMAIL_PASS sea la clave de 16 letras de Google, no tu clave normal.")
    else:
        logger.error("No se encontró el archivo ZIP.")

if __name__ == "__main__":
    enviar_reporte()
