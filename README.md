# ADT TEST — Automatización de Auditoría de Asistencia

Suite de automatización con Selenium que genera, descarga y valida reportes de asistencia laboral desde el portal [asistenciadt.baplicada.cl](https://asistenciadt.baplicada.cl) para 13 empresas clientes.

## ¿Qué hace?

Por cada empresa configurada, el sistema:

1. Inicia sesión en el portal
2. Selecciona la empresa por RUT
3. Genera y descarga 6 tipos de reporte (PDF y/o Excel)
4. Valida los datos del reporte de Jornada Diaria contra cálculos esperados
5. Captura evidencia en imagen PNG del PDF:
   - **Auditoría OK** → imagen con todas las páginas del primer empleado
   - **Auditoría FAIL** → imagen de las páginas del empleado con error
6. Genera un reporte HTML con el resumen de resultados
7. Consolida todo en un ZIP y lo envía por email

## Reportes generados por empresa

| Clave | Descripción |
|-------|-------------|
| `asistencia` | Reporte de asistencia general |
| `jor_diaria` | Jornada diaria (incluye auditoría de horas) |
| `domingos` | Trabajo en domingos y festivos |
| `modificaciones` | Modificaciones de turno |
| `diario` | Reporte diario |
| `incidentes` | Incidentes técnicos |

## Requisitos

### Sistema

- Python 3.13
- Google Chrome (versión estable)
- [wkhtmltopdf](https://wkhtmltopdf.org/downloads.html) — para convertir HTML a PDF
- [Poppler](https://github.com/oschwartz10612/poppler-windows/releases/) — para convertir PDF a imagen (Windows: agregar `bin/` al PATH)

### Python

```bash
pip install -r requirements.txt
```

## Variables de entorno

Crea un archivo `.env` en la raíz del proyecto (nunca lo subas al repositorio):

```env
EMAIL_USER=tu_correo@gmail.com
EMAIL_PASS=tu_app_password_de_gmail
```

> El password debe ser una [App Password de Google](https://myaccount.google.com/apppasswords), no tu contraseña normal.

Las credenciales del portal se configuran en [data/credenciales.py](data/credenciales.py).

## Estructura del proyecto

```
ADT_TEST/
├── conftest.py          # Configuración del driver de Selenium (fixtures pytest)
├── requirements.txt     # Dependencias Python
├── data/
│   ├── credenciales.py  # Usuario y contraseña del portal
│   └── empresas.py      # Lista de empresas con RUT y configuración de reportes
├── pages/               # Page Object Model
│   ├── base_page.py     # Clase base con waits y utilidades comunes
│   ├── login_page.py    # Interacciones de la pantalla de login
│   ├── init_page.py     # Selección de empresa
│   └── fisc_page.py     # Generación y descarga de reportes
├── tests/
│   ├── test_login.py    # Validación del login (credenciales válidas e inválidas)
│   ├── test_init.py     # Selección y cambio de empresa
│   └── test_reporte.py  # Flujo principal: genera reportes para las 14 empresas
├── utils/
│   ├── auditoria.py     # Valida el Excel de Jornada Diaria
│   ├── enviar_correo.py # Envío del ZIP por email (Gmail SMTP)
│   ├── helpers.py       # Limpieza de la carpeta de descargas
│   ├── pdf_converter.py # Convierte PDF a PNG: todas las páginas del primer empleado (OK) o del empleado con error (FAIL)
│   ├── pdf_merger.py    # Fusiona reportes HTML en un PDF consolidado
│   ├── report_html.py   # Genera el reporte HTML de resultados
│   ├── screenshots.py   # Captura de pantalla con timestamp
│   └── zipper.py        # Empaqueta artefactos en ZIP
├── downloads/           # Archivos descargados durante los tests (generado)
├── reports/             # Reportes HTML generados (generado)
└── screenshots/         # Evidencias de error (generado)
```

## Cómo ejecutar

### Solo el flujo de reportes (prueba principal)

```bash
pytest tests/test_reporte.py -s
```

### Todos los tests

```bash
pytest tests/ -s
```

### Una empresa específica

```bash
pytest tests/test_reporte.py -s -k "ENAP"
```

### Con reporte HTML de pytest

```bash
pytest tests/test_reporte.py -s --html=reports/resultado.html --self-contained-html
```

### Post-procesamiento manual (PDF consolidado y ZIP)

Después de correr pytest, los HTMLs quedan en `reports/`. Para generar el PDF consolidado y el ZIP ejecuta desde la raíz del proyecto en la terminal de VS Code:

**PowerShell:**
```powershell
$env:PYTHONPATH = $PWD
python utils/pdf_merger.py    # genera reports/Reporte_Consolidado_Auditoria.pdf
python utils/zipper.py        # genera Paquete_Final_YYYY-MM-DD.zip
python utils/enviar_correo.py # opcional: enviar email
```

**CMD:**
```cmd
set PYTHONPATH=%CD%
python utils/pdf_merger.py
python utils/zipper.py
python utils/enviar_correo.py
```

> `PYTHONPATH` es necesario para que los scripts encuentren los módulos internos del proyecto.

## CI/CD (GitHub Actions)

El workflow `.github/workflows/test.yml` se activa en push a `master` y `feature/mejoras`, y manualmente desde GitHub (workflow_dispatch) para el cron externo.

El pipeline:
1. Instala Chrome, wkhtmltopdf y Poppler en Ubuntu
2. Ejecuta `tests/test_reporte.py` en modo headless
3. Genera el PDF consolidado y el ZIP
4. Sube los artefactos (`Paquete-Auditoria-Final`, `evidencias-tecnicas`)
5. Envía el email con el reporte

Para el envío de email en CI, configura los secrets `EMAIL_USER` y `EMAIL_PASS` en **Settings → Secrets and variables → Actions** del repositorio.

## Empresas configuradas

| Empresa | RUT |
|---------|-----|
| ALTERNATTIVA | 79777010-8 |
| Biometria Aplicada Spa | 76257834-4 |
| CYGNUS | 77128770-0 |
| Empresa Nacional del Petroleo | 92604000-6 |
| ENAP REFINERIAS S.A | 87756500-9 |
| Enap Sipetrol S.A | 96579730-0 |
| NUEVA BIOMETRIA SPA | 77091268-7 |
| Sigdo Koppers (IC) | 91915000-9 |
| SIGDO KOPPERS S.A. | 99598300-1 |
| SIO RRHH | 78167971-2 |
| SK CAPACITACION | 76788120-7 |
| SK INDUSTRIAL | 76662490-1 |
| SKCOMSA | 96717980-9 |

**Total: 13 empresas × 6 reportes = 78 escenarios automatizados**
