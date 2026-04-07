import os
from datetime import datetime

def generar_html(resultados_empresa):
    empresa = resultados_empresa["empresa"]
    rut = resultados_empresa["rut"]
    reportes = resultados_empresa["reportes"]

    total = len(reportes)
    ok_count = sum(1 for r in reportes if r["estado"] == "OK")
    fail_count = total - ok_count

    bloques = ""

    for r in reportes:
        # Definición de colores por estado
        if r["estado"] == "OK":
            color = "#28a745"
        elif r["estado"] == "FAIL":
            color = "#dc3545"
        else:
            color = "#ffc107"  # Amarillo para NO_DATA o advertencias
        
        badge = r["estado"]

        # Generación de lista de errores
        errores_html = "".join(
            f"<li>{e}</li>" for e in r["errores"]
        ) if r["errores"] else "<li>Sin errores</li>"

        # --- CORRECCIÓN DE RUTAS PARA HTML ---
        # Reemplazamos backslashes (\) por slashes (/) para que el HTML 
        # encuentre la imagen correctamente en cualquier sistema.
        ruta_limpia = r["captura"].replace("\\", "/")
        # -------------------------------------

        bloques += f"""
        <div class="card">
            <div class="card-header">
                <h2>{r["nombre"]}</h2>
                <span class="badge" style="background:{color}">{badge}</span>
            </div>

            <div class="card-body">
                <h4>Detalle de Auditoría</h4>
                <ul class="errores">{errores_html}</ul>

                <img src="../{ruta_limpia}" class="screenshot" alt="Captura de {r['nombre']}">
            </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Reporte - {empresa}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f7fa;
                margin: 0;
                padding: 20px;
                color: #333;
            }}

            .container {{
                max-width: 1200px;
                margin: auto;
            }}

            h1 {{ margin-bottom: 5px; }}

            .header {{
                background: white;
                padding: 25px;
                border-radius: 10px;
                margin-bottom: 25px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            }}

            .summary {{
                display: flex;
                gap: 15px;
                margin-top: 15px;
            }}

            .box {{
                padding: 8px 18px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}

            .ok {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .fail {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
            .total {{ background: #e2e3e5; color: #383d41; border: 1px solid #d6d8db; }}

            .card {{
                background: white;
                margin-bottom: 25px;
                border-radius: 12px;
                box-shadow: 0 3px 12px rgba(0,0,0,0.06);
                overflow: hidden;
            }}

            .card-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 25px;
                background: #fcfcfc;
                border-bottom: 1px solid #edf2f7;
            }}

            .badge {{
                color: white;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }}

            .card-body {{ padding: 25px; }}

            .errores {{
                background: #fff3cd;
                padding: 15px;
                border-radius: 6px;
                border-left: 5px solid #ffeeba;
                list-style-position: inside;
            }}

            .screenshot {{
                margin-top: 20px;
                max-width: 100%;
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
                <h1>Informe de Auditoría Automática</h1>
                <p><b>Empresa:</b> {empresa}</p>
                <p><b>RUT:</b> {rut}</p>
                <p><b>Fecha Generación:</b> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>

                <div class="summary">
                    <div class="box total">Reportes evaluados: {total}</div>
                    <div class="box ok">Exitosos: {ok_count}</div>
                    <div class="box fail">Fallidos: {fail_count}</div>
                </div>
            </div>

            {bloques}

        </div>
    </body>
    </html>
    """

    carpeta = "reports"
    os.makedirs(carpeta, exist_ok=True)

    # Limpiamos el nombre de la empresa para el nombre de archivo
    nombre_seguro = empresa.replace(" ", "_").replace("/", "-")
    ruta = os.path.join(carpeta, f"{nombre_seguro}.html")

    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)

    return ruta