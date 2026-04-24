import os
import json
import base64
from datetime import datetime

_FORMAL_TO_KEY = {
    "Reporte de Asistencia": "asistencia",
    "Reporte de Jornada Diaria": "jor_diaria",
    "Reporte de días domingo y/o días festivos": "domingos",
    "Reporte de modificaciones y/o alteraciones de turnos": "modificaciones",
    "Reporte Diario": "diario",
    "Reporte de Incidentes Técnicos": "incidentes",
}

SUMMARY_JSON = os.path.join("reports", "summary_data.json")


def _etiqueta_celda(estado, errores, tipo_fallo=None):
    if estado == "OK":
        return "OK", "#28a745"
    if estado == "NO_DATA":
        return "SIN DATOS", "#ffc107"
    if tipo_fallo == "auditoria":
        return "AUDITORIA", "#dc3545"
    if tipo_fallo == "bdatos":
        return "BDATOS", "#dc3545"
    if tipo_fallo == "servidor":
        return "SERVIDOR", "#dc3545"
    return "TIEMPO", "#dc3545"


def _registrar_en_resumen(resultados_empresa):
    datos = []
    if os.path.exists(SUMMARY_JSON):
        try:
            with open(SUMMARY_JSON, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except Exception:
            datos = []

    entry = {
        "empresa": resultados_empresa["empresa"],
        "rut": resultados_empresa["rut"],
        "reportes": {},
    }
    for r in resultados_empresa["reportes"]:
        key = _FORMAL_TO_KEY.get(r["nombre"], r["nombre"])
        etiqueta, color = _etiqueta_celda(r["estado"], r.get("errores", []), r.get("tipo_fallo"))
        entry["reportes"][key] = {"etiqueta": etiqueta, "color": color}

    for i, d in enumerate(datos):
        if d["empresa"] == entry["empresa"]:
            datos[i] = entry
            break
    else:
        datos.append(entry)

    os.makedirs("reports", exist_ok=True)
    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

# Función para convertir la imagen a texto (Base64) - Mantenemos tu lógica
def imagen_a_base64(ruta_imagen):
    try:
        if not ruta_imagen or not os.path.exists(ruta_imagen):
            return ""
        with open(ruta_imagen, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except:
        return ""

def generar_html(resultados_empresa):
    empresa = resultados_empresa["empresa"]
    rut = resultados_empresa["rut"]
    reportes = resultados_empresa["reportes"]

    total = len(reportes)
    ok_count = sum(1 for r in reportes if r["estado"] == "OK")
    fail_count = total - ok_count

    filas_resumen = ""
    for i, r in enumerate(reportes):
        if r["estado"] == "OK":
            color_resumen = "#28a745"
        elif r["estado"] == "FAIL":
            color_resumen = "#dc3545"
        else:
            color_resumen = "#ffc107"

        filas_resumen += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">
                {r["nombre"]}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; color: {color_resumen}; font-weight: bold;">
                {r["estado"]}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                {f"Hallazgos: {len(r['errores'])}" if r['errores'] and r['estado'] == 'FAIL' else "Sin observaciones"}
            </td>
        </tr>
        """

    resumen_tabla_html = f"""
    <div class="header" style="margin-top: 20px;">
        <h2 style="color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px;">Índice de Reportes (Resumen)</h2>
        <table style="width: 100%; border-collapse: collapse; background: white;">
            <thead>
                <tr style="background: #f8f9fa; text-align: left;">
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6;">Reporte</th>
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6;">Estado</th>
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6;">Detalle rápido</th>
                </tr>
            </thead>
            <tbody>
                {filas_resumen}
            </tbody>
        </table>
    </div>
    """

    bloques = ""
    for i, r in enumerate(reportes):
        if r["estado"] == "OK":
            color = "#28a745"
        elif r["estado"] == "FAIL":
            color = "#dc3545"
        else:
            color = "#ffc107"
        
        badge = r["estado"]

        errores_html = "".join(
            f"<li>{e}</li>" for e in r["errores"]
        ) if r["errores"] else "<li>Sin hallazgos en la auditoría</li>"

        img_data = imagen_a_base64(r["captura"])
        if img_data:
            img_tag = f'<img src="data:image/png;base64,{img_data}" class="screenshot">'
        elif r["estado"] == "NO_DATA":
            img_tag = '<p style="color:gray; padding:20px; border:1px dashed #ccc; text-align:center;">Sin datos — no se generó imagen del reporte</p>'
        else:
            img_tag = '<p style="color:gray; padding:20px; border:1px dashed #ccc;">Captura no disponible</p>'

        estilo_salto = "page-break-before: always;"

        bloques += f"""
        <div class="card" style="{estilo_salto}">
            <div class="card-header">
                <h2 style="margin:0;">{r["nombre"]}</h2>
                <span class="badge" style="background:{color}">{badge}</span>
            </div>

            <div class="card-body">
                <h4 style="margin-top:0;">Resultado de Auditoría</h4>
                <ul class="errores">{errores_html}</ul>
                {img_tag}
            </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Reporte Consolidado - {empresa}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f7fa;
                margin: 0;
                padding: 20px;
                color: #333;
                /*ORRECCIÓN: Aseguramos que el body NO dispare hojas en blanco al final */
                page-break-after: avoid; 
            }}
            .container {{ 
                max-width: 1100px; 
                margin: auto;
                page-break-after: avoid;
            }}
            .header {{
                background: white;
                padding: 25px;
                border-radius: 10px;
                margin-bottom: 25px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            }}
            .summary-boxes {{ display: flex; gap: 15px; margin-top: 15px; }}
            .box {{ padding: 8px 18px; border-radius: 6px; font-weight: bold; font-size: 14px; }}
            .ok {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .fail {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
            .total {{ background: #e2e3e5; color: #383d41; border: 1px solid #d6d8db; }}

            .card {{
                background: white;
                margin-top: 40px;
                border-radius: 12px;
                box-shadow: 0 3px 12px rgba(0,0,0,0.06);
                overflow: hidden;
                /* Evitamos que una tarjeta se parta en dos hojas */
                page-break-inside: avoid;
            }}
            .card-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 25px;
                background: #fcfcfc;
                border-bottom: 1px solid #edf2f7;
            }}
            .badge {{ color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
            .card-body {{ padding: 25px; }}
            .errores {{ background: #fff3cd; padding: 15px; border-radius: 6px; border-left: 5px solid #ffeeba; list-style-position: inside; }}
            .screenshot {{
                margin-top: 20px;
                width: 100%;
                height: auto;
                border-radius: 10px;
                border: 1px solid #e2e8f0;
                display: block;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin:0; color:#2c3e50;">Informe de Auditoría Automática</h1>
                <p style="margin: 5px 0;"><b>Empresa:</b> {empresa} | <b>RUT:</b> {rut}</p>
                <p style="margin: 5px 0; color: #666;"><b>Generado:</b> {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>

                <div class="summary-boxes">
                    <div class="box total">Evaluados: {total}</div>
                    <div class="box ok">OK: {ok_count}</div>
                    <div class="box fail">Fallidos: {fail_count}</div>
                </div>
            </div>

            {resumen_tabla_html}
            {bloques}
        </div>
    </body>
    </html>
    """

    carpeta = "reports"
    os.makedirs(carpeta, exist_ok=True)
    nombre_seguro = empresa.replace(" ", "_").replace("/", "-")
    ruta = os.path.join(carpeta, f"{nombre_seguro}.html")

    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)

    _registrar_en_resumen(resultados_empresa)

    return ruta