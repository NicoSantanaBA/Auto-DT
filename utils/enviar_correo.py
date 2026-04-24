import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo_BA.jpg")

HTML_TEMPLATE = """\
<html>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;background:#f4f4f4;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:30px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">

          <!-- HEADER -->
          <tr>
            <td style="background:#1a1a2e;padding:28px 36px;">
              <p style="margin:0;color:#ffffff;font-size:22px;font-weight:bold;">
                Auditoría DT &mdash; Reporte Automático
              </p>
              <p style="margin:6px 0 0;color:#a0a0b0;font-size:13px;">{fecha}</p>
            </td>
          </tr>

          <!-- BODY -->
          <tr>
            <td style="padding:32px 36px;">
              <p style="margin:0 0 20px;color:#333333;font-size:15px;">Buenos días,</p>
              <p style="margin:0 0 20px;color:#555555;font-size:14px;line-height:1.7;">
                Se adjunta el paquete de auditoría correspondiente al día de hoy,
                generado automáticamente por el sistema de control de cumplimiento de servicios.
              </p>

              <table width="100%" cellpadding="12" cellspacing="0"
                     style="background:#f8f9fa;border-radius:6px;border-left:4px solid #e8650a;margin-bottom:24px;">
                <tr>
                  <td>
                    <p style="margin:0;color:#333;font-size:13px;line-height:1.8;">
                      <strong>&#128197; Fecha:</strong> {fecha}<br>
                      <strong>&#128230; Contenido:</strong> PDF consolidado con evidencias por empresa<br>
                      <strong>&#9989; Estado:</strong> Proceso completado
                    </p>
                  </td>
                </tr>
              </table>

              <p style="margin:0;color:#888888;font-size:12px;line-height:1.7;">
                Este mensaje es generado automáticamente. Para consultas, contactar al equipo de soporte.
              </p>
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="background:#f0f0f0;padding:24px 36px;border-top:1px solid #e0e0e0;text-align:center;">
              <img src="cid:logo_ba" alt="Biometría Aplicada" width="180"
                   style="display:block;margin:0 auto 12px;"/>
              <p style="margin:0;color:#888888;font-size:11px;line-height:1.6;">
                &copy; {year} Biometría Aplicada SPA &mdash; Sistema de Control de Cumplimiento de Servicios
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def enviar_reporte():
    remitente = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    destinatarios = [
        "joseph.cervantes@iplusd.cl",
        "nicolas.perez@baplicada.cl",
        "nicolas.santana@baplicada.cl",
        "cristian.zamora@baplicada.cl",
    ]

    if not remitente or not password:
        logger.error("Faltan EMAIL_USER o EMAIL_PASS en las variables de entorno.")
        return

    fecha = datetime.now().strftime("%d/%m/%Y")
    year = datetime.now().year

    msg = MIMEMultipart("related")
    msg["Subject"] = f"Auditoría DT — Reporte Consolidado {fecha}"
    msg["From"] = remitente
    msg["To"] = ", ".join(destinatarios)

    html_body = HTML_TEMPLATE.format(fecha=fecha, year=year)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as img_file:
            logo = MIMEImage(img_file.read())
            logo.add_header("Content-ID", "<logo_ba>")
            logo.add_header("Content-Disposition", "inline", filename="logo_BA.jpg")
            msg.attach(logo)
    else:
        logger.warning(f"Logo no encontrado en {LOGO_PATH}, se enviará sin imagen.")

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
            with open(archivo_zip, "rb") as f:
                adjunto = MIMEBase("application", "zip")
                adjunto.set_payload(f.read())
                encoders.encode_base64(adjunto)
                adjunto.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=os.path.basename(archivo_zip),
                )
                msg.attach(adjunto)

            logger.info("Conectando a smtp.gmail.com...")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
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
