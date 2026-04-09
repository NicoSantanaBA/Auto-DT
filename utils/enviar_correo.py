import smtplib
import os
from email.message import EmailMessage
from datetime import datetime

def enviar_reporte():
    remitente = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    # Puedes poner varios correos separados por coma
    destinatarios = ["joseph.cervantes@inacapmail.cl"] 

    fecha = datetime.now().strftime("%d/%m/%Y")
    
    msg = EmailMessage()
    msg['Subject'] = f'Auditoría DT - {fecha}'
    msg['From'] = remitente
    msg['To'] = ", ".join(destinatarios)
    msg.set_content(f"Hola,\n\nSe adjunta el reporte consolidado de auditoría.\n\nSaludos,\nBot de Auditoría.")

    # Buscar el ZIP
    archivo_zip = next((f for f in os.listdir(".") if f.endswith(".zip") and "Auditoria" in f), None)

    if archivo_zip:
        with open(archivo_zip, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application', subtype='zip', filename=archivo_zip)

        try:
            # --- CONFIGURACIÓN PARA OUTLOOK ---
            server = smtplib.SMTP('smtp.office365.com', 587)
            server.starttls() # Seguridad obligatoria para Outlook
            server.login(remitente, password)
            server.send_message(msg)
            server.quit()
            print("Correo enviado vía Outlook con éxito.")
        except Exception as e:
            print(f"Error al enviar: {e}")
    else:
        print("No se encontró el ZIP.")

if __name__ == "__main__":
    enviar_reporte()