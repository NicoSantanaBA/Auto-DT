import smtplib
import os
from email.message import EmailMessage
from datetime import datetime

def enviar_reporte():
    # 1. Obtener credenciales desde GitHub Secrets
    remitente = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    destinatarios = ["joseph.cervantes@inacapmail.cl"] 

    if not remitente or not password:
        print(" Error: Faltan EMAIL_USER o EMAIL_PASS en los Secretos de GitHub.")
        return

    fecha = datetime.now().strftime("%d/%m/%Y")
    
    # 2. Configurar el correo
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

    # 3. Buscador de archivos ZIP (Raíz o carpeta reports)
    archivo_zip = None
    print(" Buscando el archivo ZIP...")
    for ruta in [".", "reports"]:
        if os.path.exists(ruta):
            for f in os.listdir(ruta):
                nombre_f = f.lower()
                if nombre_f.endswith(".zip") and ("paquete" in nombre_f or "auditoria" in nombre_f):
                    archivo_zip = os.path.join(ruta, f)
                    break
        if archivo_zip: break

    if archivo_zip:
        print(f" Archivo detectado: {archivo_zip}")
        try:
            with open(archivo_zip, 'rb') as f:
                msg.add_attachment(
                    f.read(),
                    maintype='application',
                    subtype='zip',
                    filename=os.path.basename(archivo_zip)
                )

            # --- CONFIGURACIÓN ESPECÍFICA PARA GMAIL ---
            print("Conectando a smtp.gmail.com...")
            # Gmail usa SSL en el puerto 465 para conexiones seguras directas
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                print(f"Intentando login con {remitente}...")
                server.login(remitente, password)
                server.send_message(msg)
            
            print("¡EL CORREO SE ENVIÓ CORRECTAMENTE!")
            
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
            print("\n Tip: Asegúrate de que EMAIL_PASS sea la clave de 16 letras de Google, no tu clave normal.")
    else:
        print(" Error: No se encontró el archivo ZIP.")

if __name__ == "__main__":
    enviar_reporte()