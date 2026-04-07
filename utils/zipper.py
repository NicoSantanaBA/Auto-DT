import zipfile
import os
from datetime import datetime

def crear_zip_auditoria(directorio_fuente, nombre_base="Auditoria"):
    fecha = datetime.now().strftime("%Y-%m-%d")
    nombre_zip = f"{nombre_base}_{fecha}.zip"
    
    # Creamos el ZIP en la raíz del proyecto
    with zipfile.ZipFile(nombre_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        encontrados = 0
        for raiz, dirs, archivos in os.walk(directorio_fuente):
            for archivo in archivos:
                # SOLO queremos los PDFs en el paquete final
                if archivo.endswith(".pdf"):
                    ruta_completa = os.path.join(raiz, archivo)
                    # Lo guardamos sin la estructura de carpetas interna
                    zipf.write(ruta_completa, archivo)
                    encontrados += 1
        
    if encontrados > 0:
        print(f"ZIP creado: {nombre_zip} (Contiene {encontrados} reportes)")
        return nombre_zip
    else:
        print("No se encontraron PDFs para comprimir.")
        return None

# En utils/zipper.py, cambia la parte de abajo:

if __name__ == "__main__":
    # En lugar de "reports", busquemos en la raíz "." 
    # pero asegúrate de filtrar para que solo agarre el PDF consolidado
    crear_zip_auditoria(".", "Paquete_Final")