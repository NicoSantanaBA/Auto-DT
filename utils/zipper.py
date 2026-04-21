import zipfile
import os
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

def crear_zip_auditoria(ruta_pdf, nombre_base="Auditoria"):
    """Empaqueta únicamente el PDF consolidado indicado en un ZIP."""
    if not os.path.exists(ruta_pdf):
        logger.error(f"No se encontró el PDF a comprimir: {ruta_pdf}")
        return None

    fecha = datetime.now().strftime("%Y-%m-%d")
    nombre_zip = f"{nombre_base}_{fecha}.zip"

    with zipfile.ZipFile(nombre_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(ruta_pdf, os.path.basename(ruta_pdf))

    logger.info(f"ZIP creado: {nombre_zip}")
    return nombre_zip

if __name__ == "__main__":
    ruta_consolidado = os.path.join("reports", "Reporte_Consolidado_Auditoria.pdf")
    crear_zip_auditoria(ruta_consolidado, "Paquete_Final")
