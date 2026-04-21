import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="function")
def driver():
    # 1. Configuración de rutas
    download_path = os.path.abspath("downloads")
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    options = webdriver.ChromeOptions()

    #  CONFIGURACIÓN DE CI (GitHub Actions / Linux)
    if os.getenv("CI"):
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # VITAL: Desactivar GPU evita que Selenium se "congele" en Linux
        options.add_argument("--disable-gpu") 
        options.add_argument("--window-size=1920,1080")
        
        # Anti-detección: Evita que el portal bloquee al bot por ser "headless"
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")
        
        # Elimina el banner de "Un software automatizado..." que a veces tapa botones
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

    # 2. Preferencias de descarga
    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        # Forzar a que no abra el visor de PDF interno y lo descargue
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "download.extensions_to_open": "applications/pdf",
        "safebrowsing.disable_download_protection": True,
    }
    options.add_experimental_option("prefs", prefs)

    # 3. Inicialización del Driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Timeouts extendidos para empresas grandes (ej. Sigdo Koppers)
    # que generan reportes pesados y pueden superar los valores por defecto.
    driver.set_page_load_timeout(300)   # 5 minutos para carga de página
    driver.set_script_timeout(120)      # 2 minutos para ejecuciones JS

    # Solo maximizar en local (en CI el window-size ya hace el trabajo)
    if not os.getenv("CI"):
        driver.maximize_window()

    yield driver

    # 4. Cierre limpio
    driver.quit()