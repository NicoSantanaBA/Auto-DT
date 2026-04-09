import smtplib
import os
from email.message import EmailMessage
from datetime import datetime

def enviar_reporte():
    # 1. Obtener credenciales
    remitente = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    destinatarios = ["joseph.cervantes@inacapmail.cl"] 

    if not remitente or not password:
        print("Error: Faltan EMAIL_USER o EMAIL_PASS en los Secretos de GitHub.")
        return

    fecha = datetime.now().strftime("%d/%m/%Y")
    
    # 2. Configurar el correo
    msg = EmailMessage()
    msg['Subject'] = f'Auditoría DT Completada - {fecha}'
    msg['From'] = remitente
    msg['To'] = ", ".join(destinatarios)
    msg.set_content(f"Hola,\n\nSe adjunta el reporte consolidado de auditoría generado hoy {fecha}.\n\nSaludos,\nBot de Auditoría Automática.")

    # 3. Buscador de archivos
    archivo_zip = None
    print("Buscando el archivo ZIP...")
    for ruta in [".", "reports"]:
        if os.path.exists(ruta):
            for f in os.listdir(ruta):
                nombre_f = f.lower()
                if nombre_f.endswith(".zip") and ("paquete" in nombre_f or "auditoria" in nombre_f):
                    archivo_zip = os.path.join(ruta, f)
                    break
        if archivo_zip: break

    if archivo_zip:
        print(f"Archivo detectado: {archivo_zip}")
        try:
            with open(archivo_zip, 'rb') as f:
                msg.add_attachment(
                    f.read(),
                    maintype='application',
                    subtype='zip',
                    filename=os.path.basename(archivo_zip)
                )

            # --- CONFIGURACIÓN SEGÚN DOCUMENTACIÓN OFICIAL DE OUTLOOK.COM ---
            # Cambiamos smtp.office365.com por smtp-mail.outlook.com
            print("Conectando a smtp-mail.outlook.com...")
            server = smtplib.SMTP('smtp-mail.outlook.com', 587)
            server.starttls()  # Protocolo STARTTLS requerido
            
            print(f"Intentando login con {remitente}...")
            server.login(remitente, password)
            
            server.send_message(msg)
            server.quit()
            print("¡EL CORREO SE ENVIÓ CORRECTAMENTE!")
            
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
            print("\nPASO FINAL OBLIGATORIO:")
            print("Si el error persiste, entra a https://account.live.com/activity")
            print("Busca el intento de 'Inicio de sesión' de GitHub y dale a 'FUI YO'.")
    else:
        print("Error: No se encontró el archivo ZIP.")

if __name__ == "__main__":
    enviar_reporte()