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
    """Error en la generación del reporte — FAIL inmediato, sin recovery."""
    def __init__(self, message, errores_lista=None):
        super().__init__(message)
        self.errores_lista = errores_lista if errores_lista is not None else [message]


class RecoverableError(Exception):
    """Error de carga de página — activa recovery (volver al selector de empresa)."""
    pass


class ConexionError(ReporteError):
    """Error de conexión con la BD — FAIL inmediato + session recovery antes del siguiente reporte."""
    pass


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
        raise RecoverableError("Pantalla en blanco: el formulario del reporte no cargó")

    if empresa["filtro_cargo"] and reporte not in ["diario", "incidentes"]:
        fisc.seleccionar_cargo(empresa["Cargo"])
        print(f"    ✓ Cargo filtrado: {empresa['Cargo']}")

    if not fisc.verificar_empresa(empresa["nom_informe"]):
        raise RecoverableError(
            f"Sesión en empresa incorrecta antes de generar reporte ({nombre_formal})"
        )

    ok_reporte, tipo_alerta = fisc.generar_reporte()

    # ── Alerta detectada: tomar captura AHORA antes de que el toast desaparezca ──
    # generar_reporte() retornó sin llamar wait_loader() cuando hay toast,
    # así que el toast todavía está visible en este punto.
    if tipo_alerta == "error_conexion":
        print(f"    ✗ Error de conexión en {nombre_formal}")
        time.sleep(0.5)
        captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error_conexion")
        time.sleep(3)
        fisc.wait_loader()
        raise ConexionError("Error de conexión con la base de datos")

    if tipo_alerta == "sin_datos":
        print(f"    {nombre_formal} sin datos")
        time.sleep(0.5)
        captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_sin_datos")
        time.sleep(3)
        fisc.wait_loader()
        return "NO_DATA", ["No hay trabajadores para este reporte"], captura

    if not ok_reporte:
        raise RecoverableError("Botón Generar Reporte no apareció")

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
                break

            except RecoverableError as e:
                # ── Botón no encontrado / Pantalla en blanco → recovery ────
                error_msg = str(e)
                print(f"    ✗ {nombre_formal} (intento {intento + 1}/2): {error_msg}")

                if intento == 0:
                    captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error_intento1")
                    print(f"    ↺ Recuperando: volviendo al selector de empresas...")
                    driver.execute_script('window.stop();')
                    driver.get("https://asistenciadt.baplicada.cl/Login.aspx?FiscalizacionDT=Login")
                    time.sleep(3)
                    init.seleccionar_empresa_por_rut(empresa["rut"])
                    init.fisc_init()
                    init.confirm()
                    time.sleep(3)
                    print(f"    ↺ Segundo intento para: {nombre_formal}")
                else:
                    print(f"    ✗✗ Segundo intento fallido para {nombre_formal}")
                    estado = "FAIL"
                    errores_lista = [error_msg]
                    errores_empresa.append(f"{nombre_formal}: {error_msg}")
                    captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error_final")

            except ConexionError as e:
                # ── Error de conexión BD → FAIL inmediato + session recovery ──
                # La sesión del servidor queda corrupta tras este error;
                # re-seleccionamos la empresa para restaurarla antes del siguiente reporte.
                error_msg = str(e)
                print(f"    ✗ {nombre_formal}: {error_msg}")
                estado = "FAIL"
                errores_lista = [error_msg]
                errores_empresa.append(f"{nombre_formal}: {error_msg}")
                print(f"    ↺ Restaurando sesión: volviendo al selector de empresas...")
                driver.execute_script('window.stop();')
                driver.get("https://asistenciadt.baplicada.cl/Login.aspx?FiscalizacionDT=Login")
                time.sleep(3)
                init.seleccionar_empresa_por_rut(empresa["rut"])
                init.fisc_init()
                init.confirm()
                time.sleep(3)
                break

            except Exception as e:
                # ── Cualquier otro error → FAIL inmediato, sin recovery ────
                error_msg = str(e)
                errores_lista = getattr(e, 'errores_lista', [error_msg])
                print(f"    ✗ {nombre_formal}: {error_msg}")
                estado = "FAIL"
                errores_empresa.append(f"{nombre_formal}: {error_msg}")
                captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error")
                break

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
