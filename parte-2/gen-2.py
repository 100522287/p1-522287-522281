#!/usr/bin/env python3

import sys
import subprocess
import re
import os

def validar_argumentos():
    """Valida los argumentos de entrada del script."""
    if len(sys.argv) != 3:
        print("Uso: python gen-buses.py <fichero-entrada> <fichero-salida>")
        sys.exit(1)
    return sys.argv[1], sys.argv[2]

def leer_fichero_entrada(fichero_entrada):
    """Lee y parsea el fichero de entrada con las dimensiones y matrices."""
    try:
        with open(fichero_entrada, "r") as fichero:
            lineas = [linea.strip() for linea in fichero.readlines() if linea.strip()]
        
        # Primera línea: dimensiones (n franjas, m autobuses, u talleres)
        n, m, u = map(int, lineas[0].split())
        
        # Leer matriz C (m x m) - Pasajeros compartidos
        matriz_c = []
        cursor = 1
        for i in range(m):
            fila = list(map(int, lineas[cursor].split()))
            if len(fila) != m:
                raise ValueError(f"Matriz C inválida: fila {i+1} tiene {len(fila)} elementos, esperados {m}")
            matriz_c.append(fila)
            cursor += 1
        
        # Leer matriz O (n x u) - Disponibilidad
        matriz_o = []
        for i in range(n):
            fila = list(map(int, lineas[cursor].split()))
            if len(fila) != u:
                raise ValueError(f"Matriz O inválida: fila {i+1} tiene {len(fila)} elementos, esperados {u}")
            matriz_o.append(fila)
            cursor += 1
        
        return n, m, u, matriz_c, matriz_o
    
    except Exception as e:
        print(f"Error al leer el fichero de entrada: {e}")
        sys.exit(1)

def escribir_fichero_datos(fichero_salida, n, m, u, matriz_c, matriz_o):
    """Genera el fichero de datos en formato AMPL/GLPK."""
    try:
        with open(fichero_salida, "w") as f:
            f.write("data;\n\n")
            
            # Declarar sets
            f.write(f"set BUSES := {' '.join(str(i) for i in range(1, m + 1))};\n")
            f.write(f"set SLOTS := {' '.join(str(i) for i in range(1, n + 1))};\n")
            f.write(f"set WORKSHOP := {' '.join(str(i) for i in range(1, u + 1))};\n\n")
            
            # Matriz C (pasajeros compartidos)
            f.write(f"param c : {' '.join(str(i) for i in range(1, m + 1))} :=\n")
            for i in range(m):
                f.write(f"{i + 1} {' '.join(str(matriz_c[i][j]) for j in range(m))}\n")
            f.write(";\n\n")
            
            # Matriz O (disponibilidad)
            f.write(f"param o : {' '.join(str(i) for i in range(1, u + 1))} :=\n")
            for i in range(n):
                f.write(f"{i + 1} {' '.join(str(matriz_o[i][j]) for j in range(u))}\n")
            f.write(";\n\n")
            
            f.write("end;\n")
    
    except Exception as e:
        print(f"Error al escribir el fichero de datos: {e}")
        sys.exit(1)

def calcular_estadisticas(n, m, u):
    """Calcula el número esperado de variables y restricciones."""
    num_variables = m * n * u + (m * (m - 1) // 2) * n
    num_restricciones = m + n * u + 3 * (m * (m - 1) // 2) * n
    return num_variables, num_restricciones

def parsear_salida_glpk(fichero_temporal):
    """Extrae información relevante del fichero de salida de GLPK."""
    patron_objetivo = re.compile(r"Objective:\s+\w+\s+=\s+([0-9]+(?:\.[0-9]+)?)")
    patron_status = re.compile(r"Status:\s+(\w+)")
    patron_rows = re.compile(r"Rows:\s+(\d+)")
    patron_cols = re.compile(r"Columns:\s+(\d+)")
    patron_asignacion = re.compile(r"^\s*\d+\s+x\[(\d+),(\d+),(\d+)\]\s+\*\s+1(?:\.0+)?\s")
    
    resultado = {
        'objetivo': None,
        'status': None,
        'filas': None,
        'columnas': None,
        'asignaciones': {}
    }
    
    with open(fichero_temporal, "r") as f:
        for linea in f:
            if match := patron_objetivo.search(linea):
                resultado['objetivo'] = float(match.group(1))
            elif match := patron_status.search(linea):
                resultado['status'] = match.group(1)
            elif match := patron_rows.search(linea):
                resultado['filas'] = int(match.group(1))
            elif match := patron_cols.search(linea):
                resultado['columnas'] = int(match.group(1))
            elif match := patron_asignacion.search(linea):
                bus = int(match.group(1))
                franja = int(match.group(2))
                taller = int(match.group(3))
                resultado['asignaciones'][bus] = (franja, taller)
    
    return resultado

def mostrar_resultados(resultado, m, num_vars_est, num_rest_est):
    """Muestra los resultados en consola."""
    # Estado del modelo
    if resultado['status']:
        print(f"Estado del modelo: {resultado['status']}")
    
    # Valor objetivo
    if resultado['objetivo'] is not None:
        print(f"Objetivo (Impacto mínimo): {resultado['objetivo']}")
    else:
        print("No se pudo obtener solución óptima")
    
    # Estadísticas del modelo
    if resultado['filas'] and resultado['columnas']:
        print(f"Número de restricciones: {resultado['filas']}")
        print(f"Número de variables: {resultado['columnas']}")
    else:
        print(f"Número de variables (estimado): {num_vars_est}")
        print(f"Número de restricciones (estimado): {num_rest_est}")
    
    # Asignaciones
    print("\n---------ASIGNACIONES---------")
    for i in range(1, m + 1):
        if i in resultado['asignaciones']:
            franja, taller = resultado['asignaciones'][i]
            print(f"Autobús Bus{i} asignado a Franja{franja} del Taller{taller}")
        else:
            print(f"Error: autobús Bus{i} NO asignado. Revisar el parsing o el modelo.")

def resolver_modelo(fichero_modelo, fichero_datos, fichero_temporal, n, m, u):
    """Ejecuta GLPK y procesa los resultados."""
    comando = ["glpsol", "-m", fichero_modelo, "-d", fichero_datos, "-o", fichero_temporal]
    
    try:
        subprocess.run(comando, capture_output=True, text=True, check=True)
        
        num_vars_est, num_rest_est = calcular_estadisticas(n, m, u)
        resultado = parsear_salida_glpk(fichero_temporal)
        mostrar_resultados(resultado, m, num_vars_est, num_rest_est)
    
    except subprocess.CalledProcessError:
        print("Error al ejecutar GLPK. El problema podría ser infactible o no acotado.")
    except FileNotFoundError:
        print("Error: El ejecutable 'glpsol' no se encontró. ¿Está GLPK instalado y en PATH?")
    except Exception as e:
        print(f"Error inesperado durante la ejecución: {e}")
    finally:
        # Limpiar fichero temporal
        if os.path.exists(fichero_temporal):
            try:
                os.remove(fichero_temporal)
            except Exception:
                pass

def main():
    """Función principal del script."""
    # Configuración
    fichero_entrada, fichero_salida = validar_argumentos()
    fichero_modelo = "parte-2-2.mod"
    fichero_temporal = "fichero-temporal"
    
    # Leer datos de entrada
    n, m, u, matriz_c, matriz_o = leer_fichero_entrada(fichero_entrada)
    
    # Generar fichero de datos
    escribir_fichero_datos(fichero_salida, n, m, u, matriz_c, matriz_o)
    
    # Resolver modelo
    resolver_modelo(fichero_modelo, fichero_salida, fichero_temporal, n, m, u)

if __name__ == "__main__":
    main()