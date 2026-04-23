import pdfkit
import os
import re
import platform
from pdf2image import convert_from_path
from PIL import Image
from PyPDF2 import PdfReader
from utils.logger import get_logger

logger = get_logger(__name__)

POPPLER_PATH_WINDOWS = r"C:\poppler-25.12.0\Library\bin"


def _paginas_primer_empleado(pdf_path):
    """Retorna (primera, ultima) páginas 1-indexed del primer empleado, detectando por RUT."""
    try:
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            if not reader.pages:
                return 1, 1
            texto_p1 = reader.pages[0].extract_text() or ""
            match = re.search(r'RUT[:\s]+(\d{6,8}-[\dkK])', texto_p1)
            if not match:
                return 1, 1
            rut_emp1 = match.group(1)
            ultima = 1
            for i in range(1, len(reader.pages)):
                texto = reader.pages[i].extract_text() or ""
                m = re.search(r'RUT[:\s]+(\d{6,8}-[\dkK])', texto)
                if m and m.group(1) != rut_emp1:
                    break
                ultima = i + 1
            return 1, ultima
    except Exception as e:
        logger.warning(f"No se pudo detectar páginas del empleado: {e}")
        return 1, 1


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


def _paginas_por_nombre(pdf_path, nombre):
    """Retorna (primera, ultima) páginas 1-indexed del empleado cuyo nombre aparece en el header."""
    try:
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            nombre_lower = nombre.lower()
            primera = None
            ultima = None
            for i, page in enumerate(reader.pages):
                texto = (page.extract_text() or "").lower()
                if nombre_lower in texto:
                    if primera is None:
                        primera = i + 1
                    ultima = i + 1
                elif primera is not None:
                    break
            return (primera, ultima) if primera else (1, 1)
    except Exception as e:
        logger.warning(f"No se pudo localizar al empleado '{nombre}' en el PDF: {e}")
        return 1, 1


def _convertir_paginas_a_imagen(pdf_path, primera, ultima, output_dir, nombre_base, dpi):
    """Convierte un rango de páginas a una imagen PNG combinada verticalmente."""
    kwargs = {"dpi": dpi, "first_page": primera, "last_page": ultima}
    if platform.system() == "Windows" and os.environ.get("CI") != "true":
        kwargs["poppler_path"] = POPPLER_PATH_WINDOWS

    imagenes = convert_from_path(pdf_path, **kwargs)
    if not imagenes:
        return None

    os.makedirs(output_dir, exist_ok=True)
    img_path = os.path.join(output_dir, f"{nombre_base}.png")

    if len(imagenes) == 1:
        imagenes[0].save(img_path, "PNG")
    else:
        ancho = max(img.width for img in imagenes)
        alto_total = sum(img.height for img in imagenes)
        combinada = Image.new("RGB", (ancho, alto_total), (255, 255, 255))
        y = 0
        for img in imagenes:
            combinada.paste(img, (0, y))
            y += img.height
        combinada.save(img_path, "PNG")

    return img_path


def pdf_primer_empleado_a_imagen(pdf_path, output_dir, nombre_base, dpi=200):
    """Convierte todas las páginas del primer empleado a una imagen PNG combinada."""
    try:
        primera, ultima = _paginas_primer_empleado(pdf_path)
        logger.info(f"Primer empleado ocupa páginas {primera}-{ultima}")
        return _convertir_paginas_a_imagen(pdf_path, primera, ultima, output_dir, nombre_base, dpi)
    except Exception as e:
        logger.error(f"Error generando imagen multi-página: {e}")
        return None


def pdf_empleado_error_a_imagen(pdf_path, output_dir, nombre_base, nombre_empleado, dpi=200):
    """Captura todas las páginas del empleado con error, identificado por nombre."""
    try:
        primera, ultima = _paginas_por_nombre(pdf_path, nombre_empleado)
        logger.info(f"Empleado '{nombre_empleado}' ocupa páginas {primera}-{ultima}")
        return _convertir_paginas_a_imagen(pdf_path, primera, ultima, output_dir, nombre_base, dpi)
    except Exception as e:
        logger.error(f"Error generando imagen de empleado con error: {e}")
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
