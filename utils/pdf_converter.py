import pdfkit
import os
import platform
from pdf2image import convert_from_path
from utils.logger import get_logger

logger = get_logger(__name__)

POPPLER_PATH_WINDOWS = r"C:\poppler-25.12.0\Library\bin"


def pdf_pagina1_a_imagen(pdf_path, output_dir, nombre_base, dpi=200):
    """Convierte la primera página de un PDF a imagen PNG de alta calidad."""
    try:
        kwargs = {"dpi": dpi, "first_page": 1, "last_page": 1}
        if platform.system() == "Windows" and os.environ.get("CI") != "true":
            kwargs["poppler_path"] = POPPLER_PATH_WINDOWS

        imagenes = convert_from_path(pdf_path, **kwargs)
        if not imagenes:
            return None
        os.makedirs(output_dir, exist_ok=True)
        img_path = os.path.join(output_dir, f"{nombre_base}.png")
        imagenes[0].save(img_path, "PNG")
        return img_path
    except Exception as e:
        logger.error(f"Error convirtiendo PDF a imagen: {e}")
        return None

def convertir_html_a_pdf(directorio_reportes):
    if platform.system() == "Windows":
        path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    else:
        config = pdfkit.configuration()

    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'no-outline': None,
        'quiet': ''
    }

    logger.info("Iniciando conversión a PDF...")

    for archivo in os.listdir(directorio_reportes):
        if archivo.endswith(".html"):
            ruta_html = os.path.join(directorio_reportes, archivo)
            ruta_pdf = ruta_html.replace(".html", ".pdf")

            try:
                pdfkit.from_file(ruta_html, ruta_pdf, options=options, configuration=config)
                logger.info(f"Convertido: {archivo} -> PDF")
            except Exception as e:
                logger.error(f"Error en {archivo}: {e}")

if __name__ == "__main__":
    convertir_html_a_pdf("reports")
