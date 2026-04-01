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
        color = "#28a745" if r["estado"] == "OK" else "#dc3545"
        badge = "OK" if r["estado"] == "OK" else "FAIL"

        errores_html = "".join(
            f"<li>{e}</li>" for e in r["errores"]
        ) if r["errores"] else "<li>Sin errores</li>"

        bloques += f"""
        <div class="card">
            <div class="card-header">
                <h2>{r["nombre"]}</h2>
                <span class="badge" style="background:{color}">{badge}</span>
            </div>

            <div class="card-body">
                <h4>Errores</h4>
                <ul class="errores">{errores_html}</ul>

                <img src="../{r["captura"]}" class="screenshot">
            </div>
        </div>
        """

    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Arial;
                background: #f5f7fa;
                margin: 0;
                padding: 20px;
            }}

            .container {{
                max-width: 1200px;
                margin: auto;
            }}

            h1 {{
                margin-bottom: 5px;
            }}

            .header {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }}

            .summary {{
                display: flex;
                gap: 20px;
                margin-top: 10px;
            }}

            .box {{
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }}

            .ok {{ background: #d4edda; color: #155724; }}
            .fail {{ background: #f8d7da; color: #721c24; }}
            .total {{ background: #e2e3e5; }}

            .card {{
                background: white;
                margin-bottom: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                overflow: hidden;
            }}

            .card-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                border-bottom: 1px solid #eee;
            }}

            .badge {{
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 12px;
            }}

            .card-body {{
                padding: 20px;
            }}

            .errores {{
                background: #fff3cd;
                padding: 10px;
                border-radius: 5px;
            }}

            .screenshot {{
                margin-top: 15px;
                max-width: 100%;
                border-radius: 8px;
                border: 1px solid #ddd;
            }}
        </style>
    </head>

    <body>
        <div class="container">

            <div class="header">
                <h1>Informe de Auditoría</h1>
                <p><b>Empresa:</b> {empresa}</p>
                <p><b>RUT:</b> {rut}</p>
                <p><b>Fecha:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

                <div class="summary">
                    <div class="box total">Total: {total}</div>
                    <div class="box ok">OK: {ok_count}</div>
                    <div class="box fail">FAIL: {fail_count}</div>
                </div>
            </div>

            {bloques}

        </div>
    </body>
    </html>
    """

    carpeta = "reports"
    os.makedirs(carpeta, exist_ok=True)

    ruta = os.path.join(carpeta, f"{empresa.replace(' ', '_')}.html")

    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)

    return ruta