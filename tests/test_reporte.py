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


@pytest.mark.parametrize("empresa", EMPRESAS, ids=[e["nombre"] for e in EMPRESAS])
def test_reporte(driver, empresa):

    download_path = "C:\\Users\\PrDes\\Desktop\\ADT_TEST\\downloads"
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

        print(f"\n>>> Iniciando reporte: {reporte}")

        try:
            fisc.seleccionar_reporte(reporte)

            if empresa["filtro_cargo"] and reporte not in ["diario", "incidentes"]:
                fisc.seleccionar_cargo(empresa["Cargo"])
                print(f"    ✓ Cargo filtrado: {empresa['Cargo']}")

            # NUEVO: validar generación
            ok_reporte = fisc.generar_reporte()

            if not ok_reporte:
                print(f"    ✗ No apareció botón generar reporte")

                estado = "FAIL"
                errores_lista.append("Botón Generar Reporte no apareció")
                errores_empresa.append(f"{reporte}: no se pudo generar reporte")

                captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error")

                resultados_empresa["reportes"].append({
                    "nombre": reporte,
                    "estado": estado,
                    "errores": errores_lista,
                    "captura": captura
                })

                continue  # siguiente reporte

            # captura SIEMPRE después de generar
            captura = guardar_captura(driver, empresa["nombre"], reporte)

            time.sleep(3)

            if not fisc.reporte_tiene_datos():
                print(f"    ✗ Reporte {reporte} no cargó")

                estado = "FAIL"
                errores_lista.append("No cargó el reporte")
                errores_empresa.append(f"{reporte}: no cargó")

            else:
                print(f"    ✓ Reporte generado: {reporte}")

                if reporte == "jor_diaria":
                    archivo = fisc.descargar_excel(download_path)

                    if not archivo:
                        print(f"    ✗ No se descargó archivo")

                        estado = "FAIL"
                        errores_lista.append("No se descargó archivo")
                        errores_empresa.append(f"{reporte}: No se descargó archivo")

                    else:
                        print(f"    ✓ Archivo descargado: {archivo}")

                        ok, errores = auditar_excel_final(archivo)

                        if ok:
                            print("    ✓ Auditoría OK")
                        else:
                            print(f"    ✗ Auditoría FALLÓ: {errores}")

                            estado = "FAIL"
                            errores_lista = errores
                            errores_empresa.append(f"{reporte}: {errores}")

        except Exception as e:
            print(f"Error inesperado en {reporte}: {e}")

            estado = "FAIL"
            errores_lista.append(str(e))
            errores_empresa.append(f"{reporte}: {e}")

            captura = guardar_captura(driver, empresa["nombre"], f"{reporte}_error")

        # SIEMPRE guardar resultado
        resultados_empresa["reportes"].append({
            "nombre": reporte,
            "estado": estado,
            "errores": errores_lista,
            "captura": captura
        })

    # SIEMPRE generar HTML
    ruta_html = generar_html(resultados_empresa)
    print(f"\nReporte generado: {ruta_html}")

    # ASSERT FINAL
    assert not errores_empresa, f"{empresa['nombre']} | {errores_empresa}"