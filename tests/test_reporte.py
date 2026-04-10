import datetime
import pytest
from conftest import driver
from data.empresas import EMPRESAS
from data.credenciales import USER
from pages.login_page import LoginPage
from pages.init_page import InitPage
from pages.fisc_page import FiscPage
from utils.helpers import limpiar_descargas
from utils.auditoria import auditar_excel_final
import time
from utils.screenshots import guardar_captura
from utils.report_html import generar_html
import os


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
        estado = "OK"
        errores_lista = []

        # 🚀 CORRECCIÓN: Usamos REPORTE_NOMBRES_FORMALES que es el que está en FiscPage
        nombre_formal = fisc.REPORTE_NOMBRES_FORMALES.get(reporte, reporte)

        print(f"\n>>> Iniciando reporte: {nombre_formal}")

        try:
            fisc.seleccionar_reporte(reporte)

            if empresa["filtro_cargo"] and reporte not in ["diario", "incidentes"]:
                fisc.seleccionar_cargo(empresa["Cargo"])
                print(f"    ✓ Cargo filtrado: {empresa['Cargo']}")

            ok_reporte = fisc.generar_reporte()

            if fisc.hay_sin_datos():
                print(f"    {nombre_formal} sin datos")

                estado = "NO_DATA"
                errores_lista.append("No hay trabajadores para este reporte")
                time.sleep(1)
                captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_sin_datos")

                resultados_empresa["reportes"].append({
                    "nombre": nombre_formal,
                    "estado": estado,
                    "errores": errores_lista,
                    "captura": captura
                })
                time.sleep(4)  # esperar que aparezca alerta y evitar solapamiento de capturas
                continue

            if not ok_reporte:
                print(f"    ✗ No apareció botón generar reporte")

                estado = "FAIL"
                errores_lista.append("Botón Generar Reporte no apareció")
                errores_empresa.append(f"{nombre_formal}: no se pudo generar reporte")

                captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error")

                resultados_empresa["reportes"].append({
                    "nombre": nombre_formal,
                    "estado": estado,
                    "errores": errores_lista,
                    "captura": captura
                })

                continue  # siguiente reporte

            # captura SIEMPRE después de generar
            captura = guardar_captura(driver, empresa["nombre"], reporte)

            time.sleep(3)

            if not fisc.reporte_tiene_datos():
                print(f"    ✗ Reporte {nombre_formal} no cargó")

                estado = "FAIL"
                errores_lista.append("No cargó el reporte")
                errores_empresa.append(f"{nombre_formal}: no cargó")

            else:
                print(f"    ✓ Reporte generado: {nombre_formal}")

                if reporte == "jor_diaria":
                    archivo = fisc.descargar_excel(download_path)

                    if not archivo:
                        print(f"    ✗ No se descargó archivo")

                        estado = "FAIL"
                        errores_lista.append("No se descargó archivo")
                        errores_empresa.append(f"{nombre_formal}: No se descargó archivo")

                    else:
                        print(f"    ✓ Archivo descargado: {archivo}")

                        ok, errores = auditar_excel_final(archivo)

                        if ok:
                            print("    ✓ Auditoría OK")
                        else:
                            print(f"    ✗ Auditoría FALLÓ: {errores}")

                            estado = "FAIL"
                            errores_lista = errores
                            errores_empresa.append(f"{nombre_formal}: {errores}")

        except Exception as e:
            print(f"Error inesperado en {nombre_formal}: {e}")

            estado = "FAIL"
            errores_lista.append(str(e))
            errores_empresa.append(f"{nombre_formal}: {e}")

            captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error")

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