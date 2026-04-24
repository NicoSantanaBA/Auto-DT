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
from utils.screenshots import guardar_captura
from utils.report_html import generar_html
from utils.pdf_converter import pdf_pagina1_a_imagen, pdf_primer_empleado_a_imagen, pdf_empleado_error_a_imagen, pdf_todas_paginas_a_imagen
from utils.logger import get_logger
import shutil
import time
import os

logger = get_logger(__name__)


class ReporteError(Exception):
    """Error en la generación del reporte — FAIL inmediato, sin recovery."""
    def __init__(self, message, errores_lista=None, captura=None):
        super().__init__(message)
        self.errores_lista = errores_lista if errores_lista is not None else [message]
        self.captura = captura


class RecoverableError(Exception):
    """Error de carga de página — activa recovery (volver al selector de empresa)."""
    pass


class SesionIncorrectaError(RecoverableError):
    """Sesión en empresa incorrecta — permite hasta 2 recuperaciones consecutivas."""
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

    if empresa["filtro_cargo"] and reporte not in ["diario", "incidentes"]:
        fisc.seleccionar_cargo(empresa["Cargo"])
        logger.info(f"Cargo filtrado: {empresa['Cargo']}")

    if not fisc.verificar_empresa(empresa["nom_informe"]):
        raise SesionIncorrectaError(
            f"Sesión en empresa incorrecta antes de generar reporte ({nombre_formal})"
        )

    ok_reporte, tipo_alerta = fisc.generar_reporte()

    if tipo_alerta == "error_conexion":
        logger.error(f"Error de conexión en {nombre_formal}")
        time.sleep(0.5)
        captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error_conexion")
        time.sleep(3)
        fisc.wait_loader()
        raise ConexionError("Error de conexión con la base de datos", captura=captura)

    if tipo_alerta == "sin_datos":
        logger.warning(f"{nombre_formal} sin datos")
        time.sleep(0.5)
        captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_sin_datos")
        time.sleep(3)
        fisc.wait_loader()
        return "NO_DATA", ["No hay trabajadores para este reporte"], captura

    if not ok_reporte:
        raise RecoverableError("Botón Generar Reporte no apareció")

    time.sleep(3)

    if not fisc.reporte_tiene_datos():
        raise RecoverableError("No cargó el reporte")

    logger.info(f"Reporte generado: {nombre_formal}")
    captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_estado")

    if fisc.hay_tabla_vacia():
        logger.info(f"Sin datos para mostrar en {nombre_formal}")
        return "OK", ["Sin datos para mostrar"], captura

    limpiar_descargas(download_path)
    screenshots_dir = os.path.join("screenshots", empresa["nombre"].replace(" ", "_"))
    pdf_guardado = None
    try:
        pdf_path = fisc.descargar_pdf(download_path)
        os.makedirs(screenshots_dir, exist_ok=True)
        pdf_guardado = os.path.join(screenshots_dir, f"{reporte}_source.pdf")
        shutil.copy2(pdf_path, pdf_guardado)
        captura_pdf = pdf_pagina1_a_imagen(pdf_path, screenshots_dir, f"{reporte}_pdf")
        if captura_pdf:
            captura = captura_pdf
        logger.info(f"Imagen del PDF generada: {captura}")
    except Exception as e_pdf:
        logger.warning(f"No se pudo obtener imagen del PDF: {e_pdf}")

    if reporte == "diario" and pdf_guardado and os.path.exists(pdf_guardado):
        try:
            captura_full = pdf_todas_paginas_a_imagen(pdf_guardado, screenshots_dir, f"{reporte}_pdf")
            if captura_full:
                captura = captura_full
                logger.info(f"Imagen completa del reporte diario generada: {captura_full}")
        except Exception as e_img:
            logger.warning(f"No se pudo generar imagen completa del diario: {e_img}")

    if reporte == "jor_diaria":
        limpiar_descargas(download_path)
        archivo = fisc.descargar_excel(download_path)

        if not archivo:
            logger.error("No se descargó archivo Excel")
            raise ReporteError("No se descargó archivo Excel")

        logger.info(f"Archivo descargado: {archivo}")
        ok, errores = auditar_excel_final(archivo)

        if ok:
            logger.info("Auditoría OK")
            if pdf_guardado and os.path.exists(pdf_guardado):
                try:
                    captura_full = pdf_primer_empleado_a_imagen(
                        pdf_guardado, screenshots_dir, f"{reporte}_pdf"
                    )
                    if captura_full:
                        captura = captura_full
                        logger.info(f"Imagen multi-página generada: {captura_full}")
                except Exception as e_img:
                    logger.warning(f"No se pudo generar imagen multi-página: {e_img}")
        else:
            logger.error(f"Auditoría FALLÓ: {errores}")
            captura_error = None
            if pdf_guardado and os.path.exists(pdf_guardado):
                import re as _re
                nombres = list(dict.fromkeys(
                    m.group(1) for e in errores
                    if (m := _re.search(r'\(([^)]+)\)', e))
                ))
                for nombre in nombres:
                    try:
                        captura_error = pdf_empleado_error_a_imagen(
                            pdf_guardado, screenshots_dir, f"{reporte}_pdf_error", nombre
                        )
                        if captura_error:
                            logger.info(f"Imagen de error generada para '{nombre}': {captura_error}")
                            break
                    except Exception as e_img:
                        logger.warning(f"No se pudo generar imagen de error para '{nombre}': {e_img}")
                if not captura_error:
                    captura_error = pdf_pagina1_a_imagen(
                        pdf_guardado, screenshots_dir, f"{reporte}_pdf_error"
                    )
                    logger.info("Imagen de error: fallback a página 1 del PDF")
            raise ReporteError(f"Auditoría fallida: {errores}", errores_lista=errores, captura=captura_error)

    return "OK", [], captura


@pytest.mark.parametrize("empresa", EMPRESAS, ids=[e["nombre"] for e in EMPRESAS])
def test_reporte(driver, empresa):
    download_path = os.path.abspath("downloads")

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    limpiar_descargas(download_path)

    errores_empresa = []

    resultados_empresa = {
        "empresa": empresa["nombre"],
        "rut": empresa["rut"],
        "reportes": []
    }

    login = LoginPage(driver)
    init = InitPage(driver)
    fisc = None
    login_intentos_max = 3

    for login_intento in range(login_intentos_max):
        try:
            login.load("https://asistenciadt.baplicada.cl/Login.aspx?FiscalizacionDT=Login")
            login.login(USER[0]["usuario"], USER[0]["password"])
            init.seleccionar_empresa_por_rut(empresa["rut"])
            init.fisc_init()
            init.confirm()
            fisc = FiscPage(driver)
            time.sleep(3)
            break
        except Exception as e:
            logger.warning(f"Sesión inicial (intento {login_intento + 1}/{login_intentos_max}): {str(e)[:200]}")
            if login_intento < login_intentos_max - 1:
                logger.warning("Reintentando en 30 segundos...")
                time.sleep(30)
            else:
                captura_login = guardar_captura(driver, empresa["nombre"], "login_error")
                error_msg = f"Error de sesión inicial tras {login_intentos_max} intentos: {str(e)[:200]}"
                logger.error(error_msg)
                for reporte_key in empresa["reportes"]:
                    nombre_formal_k = FiscPage.REPORTE_NOMBRES_FORMALES.get(reporte_key, reporte_key)
                    resultados_empresa["reportes"].append({
                        "nombre": nombre_formal_k,
                        "estado": "FAIL",
                        "errores": [error_msg],
                        "captura": captura_login,
                        "tipo_fallo": "servidor",
                    })
                ruta_html = generar_html(resultados_empresa)
                logger.info(f"Reporte HTML generado: {ruta_html}")
                pytest.fail(f"{empresa['nombre']} | Fallo en sesión inicial tras {login_intentos_max} intentos")

    for reporte in empresa["reportes"]:
        nombre_formal = fisc.REPORTE_NOMBRES_FORMALES.get(reporte, reporte)
        estado = "OK"
        errores_lista = []
        captura = None
        tipo_fallo = None

        logger.info(f">>> Iniciando reporte: {nombre_formal}")

        sesion_incorrecta_max = 3
        max_intentos_default = 2

        for intento in range(sesion_incorrecta_max):
            try:
                estado, errores_lista, captura = _intentar_reporte(
                    driver, fisc, empresa, reporte, download_path, nombre_formal
                )
                break

            except SesionIncorrectaError as e:
                error_msg = str(e)
                logger.warning(f"{nombre_formal} (intento {intento + 1}/{sesion_incorrecta_max}): {error_msg}")

                if intento < sesion_incorrecta_max - 1:
                    captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error_sesion_intento{intento + 1}")
                    logger.warning("Recuperando sesión incorrecta: volviendo al selector de empresas...")
                    try:
                        driver.execute_script('window.stop();')
                        driver.get("https://asistenciadt.baplicada.cl/Login.aspx?FiscalizacionDT=Login")
                        time.sleep(3)
                        init.seleccionar_empresa_por_rut(empresa["rut"])
                        init.fisc_init()
                        init.confirm()
                        time.sleep(3)
                        logger.info(f"Intento {intento + 2} para: {nombre_formal}")
                    except Exception as e_rec:
                        logger.error(f"Recovery de sesión fallido: {e_rec}")
                        estado = "FAIL"
                        errores_lista = [error_msg]
                        tipo_fallo = "servidor"
                        errores_empresa.append(f"{nombre_formal}: {error_msg}")
                        break
                else:
                    logger.error(f"Todos los intentos de sesión fallaron para {nombre_formal}")
                    estado = "FAIL"
                    errores_lista = [error_msg]
                    tipo_fallo = "servidor"
                    errores_empresa.append(f"{nombre_formal}: {error_msg}")
                    captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error_final")

            except (RecoverableError, LoaderTimeoutError) as e:
                error_msg = str(e)
                logger.warning(f"{nombre_formal} (intento {intento + 1}/{max_intentos_default}): {error_msg}")

                if intento == 0:
                    captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error_intento1")
                    logger.warning("Recuperando: volviendo al selector de empresas...")
                    try:
                        driver.execute_script('window.stop();')
                        driver.get("https://asistenciadt.baplicada.cl/Login.aspx?FiscalizacionDT=Login")
                        time.sleep(3)
                        init.seleccionar_empresa_por_rut(empresa["rut"])
                        init.fisc_init()
                        init.confirm()
                        time.sleep(3)
                        logger.info(f"Segundo intento para: {nombre_formal}")
                    except Exception as e_rec:
                        logger.error(f"Recovery fallido: {e_rec}")
                        estado = "FAIL"
                        errores_lista = [error_msg]
                        tipo_fallo = "tiempo"
                        errores_empresa.append(f"{nombre_formal}: {error_msg}")
                        break
                else:
                    logger.error(f"Segundo intento fallido para {nombre_formal}")
                    estado = "FAIL"
                    errores_lista = [error_msg]
                    tipo_fallo = "tiempo"
                    errores_empresa.append(f"{nombre_formal}: {error_msg}")
                    captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error_final")
                    break

            except ConexionError as e:
                error_msg = str(e)
                captura = getattr(e, 'captura', None)
                logger.error(f"{nombre_formal} (intento {intento + 1}/2): {error_msg}")

                if intento == 0:
                    logger.warning("Recuperando tras ConnectionString: volviendo al selector de empresas...")
                    try:
                        driver.execute_script('window.stop();')
                        driver.get("https://asistenciadt.baplicada.cl/Login.aspx?FiscalizacionDT=Login")
                        time.sleep(3)
                        init.seleccionar_empresa_por_rut(empresa["rut"])
                        init.fisc_init()
                        init.confirm()
                        time.sleep(3)
                        logger.info(f"Segundo intento para: {nombre_formal}")
                    except Exception as e_rec:
                        logger.error(f"Restauración de sesión fallida: {e_rec}")
                        estado = "FAIL"
                        errores_lista = [error_msg]
                        tipo_fallo = "bdatos"
                        errores_empresa.append(f"{nombre_formal}: {error_msg}")
                        break
                else:
                    logger.error(f"Segundo intento fallido para {nombre_formal} (ConnectionString)")
                    estado = "FAIL"
                    errores_lista = [error_msg]
                    tipo_fallo = "bdatos"
                    errores_empresa.append(f"{nombre_formal}: {error_msg}")
                    break

            except Exception as e:
                error_msg = str(e)
                errores_lista = getattr(e, 'errores_lista', [error_msg])
                tipo_fallo = "auditoria" if hasattr(e, 'errores_lista') else "servidor"
                logger.error(f"{nombre_formal}: {error_msg}")
                estado = "FAIL"
                errores_empresa.append(f"{nombre_formal}: {error_msg}")
                captura = getattr(e, 'captura', None) or guardar_captura(driver, empresa["nombre"], f"{reporte}_error")
                break

        resultados_empresa["reportes"].append({
            "nombre": nombre_formal,
            "estado": estado,
            "errores": errores_lista,
            "captura": captura,
            "tipo_fallo": tipo_fallo,
        })

    ruta_html = generar_html(resultados_empresa)
    logger.info(f"Reporte HTML generado: {ruta_html}")

    assert not errores_empresa, f"{empresa['nombre']} | {errores_empresa}"
