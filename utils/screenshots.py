import os
import datetime

def guardar_captura(driver, empresa, reporte):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    carpeta = os.path.join("screenshots", empresa.replace(" ", "_"))
    os.makedirs(carpeta, exist_ok=True)

    nombre = f"{reporte}_{timestamp}.png"
    ruta = os.path.join(carpeta, nombre)

    driver.save_screenshot(ruta)

    return ruta