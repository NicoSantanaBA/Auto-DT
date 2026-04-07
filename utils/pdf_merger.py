import pdfkit
import os
import platform
from PyPDF2 import PdfMerger

def generar_reporte_unico(directorio_reportes, nombre_salida="Reporte_Consolidado_Auditoria.pdf"):
    if platform.system() == "Windows":
        path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    else:
        config = pdfkit.configuration()

    merger = PdfMerger()
    pdfs_temporales = []

    print("Iniciando consolidación de reportes...")

    # 1. Convertir cada HTML a un PDF temporal
    archivos_html = sorted([f for f in os.listdir(directorio_reportes) if f.endswith(".html")])
    
    for archivo in archivos_html:
        ruta_html = os.path.join(directorio_reportes, archivo)
        ruta_pdf_temp = ruta_html.replace(".html", "_temp.pdf")
        
        try:
            pdfkit.from_file(ruta_html, ruta_pdf_temp, configuration=config)
            merger.append(ruta_pdf_temp)
            pdfs_temporales.append(ruta_pdf_temp)
            print(f"  Procesado: {archivo}")
        except Exception as e:
            print(f"  Error procesando {archivo}: {e}")

    # 2. Guardar el PDF maestro
    if pdfs_temporales:
        merger.write(nombre_salida)
        merger.close()
        print(f"\n¡ÉXITO! Reporte único creado: {nombre_salida}")

        # 3. Limpiar los PDFs temporales (opcional)
        for temp in pdfs_temporales:
            os.remove(temp)
    else:
        print("No se generaron reportes para unir.")

# En utils/pdf_merger.py, cambia la llamada final:
if __name__ == "__main__":
    # Guardarlo dentro de la carpeta reports
    ruta_final = os.path.join("reports", "Reporte_Consolidado_Auditoria.pdf")
    generar_reporte_unico("reports", nombre_salida=ruta_final)