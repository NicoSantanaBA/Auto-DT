from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, TimeoutException
import os
import time


class LoaderTimeoutError(Exception):
    """Se lanza cuando el loader no desaparece dentro del tiempo permitido."""
    pass


class BasePage:
    LOADER = (By.CSS_SELECTOR, "table.dxlpLoadingPanel_XafTheme")

    def __init__(self, driver):
        self.driver = driver

    def wait_and_type(self, locator, text, timeout=20):
        element = WebDriverWait(self.driver, timeout).until(
        EC.presence_of_element_located(locator)
    )
        element.clear()
        element.send_keys(text)
        
    def wait_and_click(self, locator, retries=3):
        for i in range(retries):
            try:
                element = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable(locator)
                )
                element.click()
                return

            except (ElementClickInterceptedException, StaleElementReferenceException):
                time.sleep(1)

        raise Exception(f"No se pudo hacer click en {locator}")

    def wait_for_visible(self, locator, timeout=20):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )

    def wait_loader(self, timeout=240):
        def loader_oculto(driver):
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, "table.dxlpLoadingPanel_XafTheme")
                if not elementos:
                    return True
                return all(
                    "display: none" in (el.get_attribute("style") or "")
                    for el in elementos
                )
            except StaleElementReferenceException:
                return False
        try:
            WebDriverWait(self.driver, timeout).until(loader_oculto)
        except TimeoutException:
            raise LoaderTimeoutError(
                f"Interrumpido por tiempo de carga excedido ({timeout}s)"
            )
    
    def wait_for_pdf(self, download_path, timeout=60):
        tiempo_inicio = time.time()
        while time.time() - tiempo_inicio < timeout:
            archivos = os.listdir(download_path)
            archivos_validos = [
                f for f in archivos
                if f.endswith(".pdf") and not f.startswith(".") and not f.endswith(".crdownload")
            ]
            if archivos_validos:
                ruta_completa = os.path.join(download_path, archivos_validos[0])
                time.sleep(2)
                if os.path.getsize(ruta_completa) > 0:
                    return ruta_completa
            time.sleep(2)
        raise Exception("No se descargó el archivo .pdf correctamente (Timeout)")

    def wait_for_file(self, download_path, timeout=60):
        tiempo_inicio = time.time()

        while time.time() - tiempo_inicio < timeout:
            archivos = os.listdir(download_path)
            
            # Filtramos para que SOLO acepte archivos que terminen en .xlsx 
            # y que NO sean temporales (.com.google... o .crdownload)
            archivos_validos = [
                f for f in archivos 
                if f.endswith(".xlsx") and not f.startswith(".") and not f.endswith(".crdownload")
            ]
            
            if archivos_validos:
                ruta_completa = os.path.join(download_path, archivos_validos[0])
                
                # Esperar un segundo extra para que el sistema de archivos suelte el archivo
                time.sleep(2) 
                
                if os.path.getsize(ruta_completa) > 0:
                    return ruta_completa

            time.sleep(2)

        raise Exception("No se descargó el archivo .xlsx correctamente (Timeout)")
    
