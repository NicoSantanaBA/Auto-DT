import pytest
from conftest import driver
from data.empresas import EMPRESAS
from data.credenciales import USER
from pages.login_page import LoginPage
from pages.init_page import InitPage
from pages.fisc_page import FiscPage
from pages.base_page import LoaderTimeoutError
from utils.helpers import limpiar_descargas
from utils.auditoria import auditar_excel_final
import time
from utils.screenshots import guardar_captura
from utils.report_html import generar_html
from utils.pdf_converter import pdf_pagina1_a_imagen
import os


class ReporteError(Exception):
    """Error en la generación del reporte. Puede transportar una lista de errores detallados."""
    def __init__(self, message, errores_lista=None):
        super().__init__(message)
        self.errores_lista = errores_lista if errores_lista is not None else [message]


def _intentar_reporte(driver, fisc, empresa, reporte, download_path, nombre_formal):
    """
    Ejecuta el flujo completo de un reporte en un único intento.

    Retorna (estado, errores_lista, captura) si el flujo termina normalmente
    (incluyendo casos NO_DATA o tabla vacía).

    Lanza ReporteError o LoaderTimeoutError si el flujo falla, para que el
    llamador pueda activar la lógica de reintento con recuperación.
    """
    captura = None

    fisc.seleccionar_reporte(reporte)

    # Detección temprana de pantalla en blanco: si el formulario no cargó,
    # no esperamos el timeout largo de generar_reporte (15 s), fallamos de inmediato.
    if fisc.pantalla_en_blanco(timeout=3):
        raise ReporteError("Pantalla en blanco: el formulario del reporte no cargó")

    if empresa["filtro_cargo"] and reporte not in ["diario", "incidentes"]:
        fisc.seleccionar_cargo(empresa["Cargo"])
        print(f"    ✓ Cargo filtrado: {empresa['Cargo']}")

    ok_reporte, tipo_alerta = fisc.generar_reporte()

    # ── Alerta detectada: tomar captura AHORA antes de que el toast desaparezca ──
    # generar_reporte() retornó sin llamar wait_loader() cuando hay toast,
    # así que el toast todavía está visible en este punto.
    if tipo_alerta == "error_conexion":
        print(f"    ✗ Error de servidor en {nombre_formal}: ConnectionString no inicializado")
        captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error_conexion")
        time.sleep(3)  # esperar que el toast desaparezca
        fisc.wait_loader()  # esperar loader pendiente
        raise ReporteError("Error de servidor: No se ha inicializado la propiedad ConnectionString")

    if tipo_alerta == "sin_datos":
        print(f"    {nombre_formal} sin datos")
        captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_sin_datos")
        time.sleep(3)  # esperar que el toast desaparezca
        fisc.wait_loader()  # esperar loader pendiente
        return "NO_DATA", ["No hay trabajadores para este reporte"], captura

    if not ok_reporte:
        raise ReporteError("Botón Generar Reporte no apareció")

    time.sleep(3)

    if not fisc.reporte_tiene_datos():
        raise ReporteError("No cargó el reporte")

    print(f"    ✓ Reporte generado: {nombre_formal}")
    captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_estado")

    if fisc.hay_tabla_vacia():
        print(f"    Sin datos para mostrar en {nombre_formal}")
        return "OK", ["Sin datos para mostrar"], captura

    # Tiene datos reales: reemplazar captura con imagen del PDF
    limpiar_descargas(download_path)
    try:
        pdf_path = fisc.descargar_pdf(download_path)
        screenshots_dir = os.path.join("screenshots", empresa["nombre"].replace(" ", "_"))
        captura_pdf = pdf_pagina1_a_imagen(pdf_path, screenshots_dir, f"{reporte}_pdf")
        if captura_pdf:
            captura = captura_pdf
        print(f"    ✓ Imagen del PDF generada: {captura}")
    except Exception as e_pdf:
        print(f"    ✗ No se pudo obtener imagen del PDF: {e_pdf}")

    if reporte == "jor_diaria":
        limpiar_descargas(download_path)
        archivo = fisc.descargar_excel(download_path)

        if not archivo:
            print(f"    ✗ No se descargó archivo")
            raise ReporteError("No se descargó archivo Excel")

        print(f"    ✓ Archivo descargado: {archivo}")
        ok, errores = auditar_excel_final(archivo)

        if ok:
            print("    ✓ Auditoría OK")
        else:
            print(f"    ✗ Auditoría FALLÓ: {errores}")
            raise ReporteError(f"Auditoría fallida: {errores}", errores_lista=errores)

    return "OK", [], captura


@pytest.mark.parametrize("empresa", EMPRESAS, ids=[e["nombre"] for e in EMPRESAS])
def test_reporte(driver, empresa):
    # Esto busca la carpeta 'downloads' en la raíz del proyecto
    download_path = os.path.abspath("downloads")

    # Asegurarnos de que la carpeta existe antes de limpiar
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    limpiar_descargas(download_path)

    # LOGIN
    login = LoginPage(driver)
    login.load("https://asistenciadt.baplicada.cl/Login.aspx?FiscalizacionDT=Login")
    login.login(USER[0]["usuario"], USER[0]["password"])

    # EMPRESA
    init = InitPage(driver)
    init.seleccionar_empresa_por_rut(empresa["rut"])
    init.fisc_init()
    init.confirm()

    fisc = FiscPage(driver)
    time.sleep(3)

    errores_empresa = []

    resultados_empresa = {
        "empresa": empresa["nombre"],
        "rut": empresa["rut"],
        "reportes": []
    }

    for reporte in empresa["reportes"]:
        nombre_formal = fisc.REPORTE_NOMBRES_FORMALES.get(reporte, reporte)
        estado = "OK"
        errores_lista = []
        captura = None

        print(f"\n>>> Iniciando reporte: {nombre_formal}")

        for intento in range(2):
            try:
                estado, errores_lista, captura = _intentar_reporte(
                    driver, fisc, empresa, reporte, download_path, nombre_formal
                )
                # Intento exitoso: salir del bucle de reintentos
                break

            except Exception as e:
                error_msg = str(e)
                # ReporteError puede llevar una lista de errores detallada;
                # para cualquier otra excepción usamos el mensaje como lista.
                errores_lista_capturados = getattr(e, 'errores_lista', [error_msg])

                print(f"    ✗ {nombre_formal} (intento {intento + 1}/2): {error_msg}")

                if intento == 0:
                    # ── Acción de Recuperación ──────────────────────────────
                    captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error_intento1")
                    print(f"    ↺ Recuperando: deteniendo carga y volviendo al selector de empresas...")
                    driver.execute_script('window.stop();')
                    driver.get("https://asistenciadt.baplicada.cl/Login.aspx?FiscalizacionDT=Login")
                    time.sleep(3)
                    init.seleccionar_empresa_por_rut(empresa["rut"])
                    init.fisc_init()
                    init.confirm()
                    time.sleep(3)
                    print(f"    ↺ Segundo intento para: {nombre_formal}")
                    # El bucle continúa con intento == 1

                else:
                    # ── Segundo intento también falló → FAIL definitivo ─────
                    print(f"    ✗✗ Segundo intento fallido para {nombre_formal}")
                    estado = "FAIL"
                    errores_lista = errores_lista_capturados
                    errores_empresa.append(f"{nombre_formal}: {error_msg}")
                    captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error_final")

        # SIEMPRE guardar resultado con el nombre formal
        resultados_empresa["reportes"].append({
            "nombre": nombre_formal,
            "estado": estado,
            "errores": errores_lista,
            "captura": captura
        })

    # SIEMPRE generar HTML
    ruta_html = generar_html(resultados_empresa)
    print(f"\nReporte generado: {ruta_html}")

    # ASSERT FINAL
    assert not errores_empresa, f"{empresa['nombre']} | {errores_empresa}"
