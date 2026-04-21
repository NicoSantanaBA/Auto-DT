import pandas as pd
import re
import os
from utils.logger import get_logger

logger = get_logger(__name__)

# CONVERSIÓN TIEMPO (Soporta objetos datetime y strings con signo)
def tiempo_a_segundos(valor):
    if pd.isna(valor) or str(valor).strip() == "" or "No Aplica" in str(valor):
        return 0
    if hasattr(valor, 'hour'):
        return valor.hour * 3600 + valor.minute * 60 + valor.second

    t = str(valor).strip().replace(" ", "").replace("+", "")
    try:
        signo = -1 if t.startswith("-") else 1
        limpio = t.replace("-", "")
        partes = limpio.split(':')
        return signo * (int(partes[0]) * 3600 + int(partes[1]) * 60 + int(partes[2]))
    except:
        return 0

# RANGO COLACIÓN DINÁMICO (Soporta nocturnos y diferentes guiones)
def calcular_duracion_colacion(rango_texto):
    if pd.isna(rango_texto) or rango_texto == "No Aplica":
        return 0
    try:
        partes = re.split(r'[-–—]', str(rango_texto).replace(" ", ""))
        if len(partes) == 2:
            inicio = tiempo_a_segundos(partes[0])
            fin = tiempo_a_segundos(partes[1])
            if inicio != 0 or fin != 0:
                return (fin - inicio + 86400) % 86400
        return 0
    except:
        return 0

# FORMATO TEXTO PARA ERRORES
def segundos_a_texto(segundos):
    signo = "-" if segundos < 0 else "+"
    abs_seg = abs(segundos)
    h, m = divmod(abs_seg, 3600)
    m, s = divmod(m, 60)
    return f"{signo}{int(h):02d}:{int(m):02d}:{int(s):02d}"

# FUNCIÓN DURACIÓN (Cruces de medianoche)
def calcular_duracion(inicio, fin):
    return (fin - inicio + 86400) % 86400

# AUDITORÍA PRINCIPAL (Limitada a 2 primeros colaboradores)
def auditar_excel_final(ruta_excel):
    try:
        ruta_ajustada = os.path.abspath(ruta_excel)
        df = pd.read_excel(ruta_ajustada, header=None)
    except Exception as e:
        return False, [f"Error al abrir archivo: {e}"]

    errores = []
    colaboradores_contados = 0
    nombre_actual = ""

    s_pactada, s_real, s_faltante, s_extra = 0, 0, 0, 0

    for i, fila in df.iterrows():
        if "Nombre:" in str(fila.values):
            colaboradores_contados += 1
            if colaboradores_contados > 2:
                break
            nombre_actual = str(fila[10]) if not pd.isna(fila[10]) else "Desconocido"

        fecha_str = str(fila[0])

        if re.match(r'\d{2}/\d{2}/\d{2}', fecha_str):
            colacion = calcular_duracion_colacion(fila[6])

            p_in = tiempo_a_segundos(fila[1])
            p_out = tiempo_a_segundos(fila[2])
            if p_in != 0 and p_out != 0:
                s_pactada += (calcular_duracion(p_in, p_out) - colacion)

            r_in = tiempo_a_segundos(fila[3])
            r_out = tiempo_a_segundos(fila[5])
            if r_in != 0 and r_out != 0:
                s_real += (calcular_duracion(r_in, r_out) - colacion)

            s_faltante += tiempo_a_segundos(fila[9])
            s_extra += tiempo_a_segundos(fila[11])

        elif "Total Semanal" in fecha_str:
            t_pact_ex = tiempo_a_segundos(fila[1])
            t_real_ex = tiempo_a_segundos(fila[3])
            t_bal_ex = tiempo_a_segundos(fila[9])

            t_bal_calc = s_extra + s_faltante
            id_info = f"Fila {i+1} ({nombre_actual})"

            if abs(s_pactada - t_pact_ex) > 10:
                errores.append(f"{id_info} | PACTADA ERROR | Esp: {segundos_a_texto(s_pactada)} | Ex: {segundos_a_texto(t_pact_ex)}")

            if abs(s_real - t_real_ex) > 10:
                errores.append(f"{id_info} | REAL ERROR | Esp: {segundos_a_texto(s_real)} | Ex: {segundos_a_texto(t_real_ex)}")

            if abs(t_bal_calc - t_bal_ex) > 10:
                errores.append(f"{id_info} | BALANCE ERROR | Esp: {segundos_a_texto(t_bal_calc)} | Ex: {segundos_a_texto(t_bal_ex)}")

            s_pactada, s_real, s_faltante, s_extra = 0, 0, 0, 0

    if errores:
        return False, errores
    return True, []

# --- BLOQUE DE PRUEBA LOCAL ---
if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ARCHIVO_PRUEBA = os.path.join(BASE_DIR, "..", "downloads", "Reporte de jornada diaria ENAP.xlsx")

    logger.info(f"Probando auditoría con: {ARCHIVO_PRUEBA}")
    resultado, lista_errores = auditar_excel_final(ARCHIVO_PRUEBA)

    if resultado:
        logger.info("Auditoría exitosa.")
    else:
        logger.error("Errores encontrados:")
        for err in lista_errores:
            logger.error(err)
