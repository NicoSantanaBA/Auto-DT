import smtplib
import os
from email.message import EmailMessage
from datetime import datetime

def enviar_reporte():
    # 1. Obtener credenciales de las variables de entorno (GitHub Secrets)
    remitente = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    destinatarios = ["joseph.cervantes@inacapmail.cl"] 

    if not remitente or not password:
        print("ERROR: No se encontraron las variables EMAIL_USER o EMAIL_PASS.")
        return

    fecha = datetime.now().strftime("%d/%m/%Y")
    
    # 2. Configurar el mensaje
    msg = EmailMessage()
    msg['Subject'] = f'Auditoría DT - {fecha}'
    msg['From'] = remitente
    msg['To'] = ", ".join(destinatarios)
    msg.set_content(f"Hola,\n\nSe adjunta el reporte consolidado de auditoría generado el {fecha}.\n\nSaludos,\nBot de Auditoría Automática.")

    # 3. BUSCADOR DE ARCHIVOS (Modificado para ser más robusto)
    archivo_zip = None
    rutas_a_revisar = [".", "reports"] # Revisa la raíz y la carpeta de reportes
    
    print("Iniciando búsqueda del reporte...")
    for ruta in rutas_a_revisar:
        if os.path.exists(ruta):
            archivos = os.listdir(ruta)
            print(f"Revisando carpeta '{ruta}': {archivos}")
            for f in archivos:
                # Busca cualquier ZIP que contenga "Auditoria" (ignorando mayúsculas/minúsculas)
                if f.lower().endswith(".zip") and "auditoria" in f.lower():
                    archivo_zip = os.path.join(ruta, f)
                    break
        if archivo_zip:
            break

    # 4. Adjuntar y enviar
    if archivo_zip:
        print(f"Archivo encontrado: {archivo_zip}")
        try:
            with open(archivo_zip, 'rb') as f:
                msg.add_attachment(
                    f.read(), 
                    maintype='application', 
                    subtype='zip', 
                    filename=os.path.basename(archivo_zip)
                )

            # --- CONEXIÓN SMTP PARA OUTLOOK ---
            print("Conectando con el servidor de Outlook...")
            server = smtplib.SMTP('smtp.office365.com', 587)
            server.starttls()  # Seguridad TLS
            server.login(remitente, password)
            server.send_message(msg)
            server.quit()
            print("¡Correo enviado con éxito!")
            
        except Exception as e:
            print(f"Error durante el envío o lectura: {e}")
    else:
        print("Error: No se encontró ningún archivo .zip que contenga 'Auditoria'.")

if __name__ == "__main__":
    enviar_reporte()