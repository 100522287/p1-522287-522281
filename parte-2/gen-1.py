#!/usr/bin/env python3

import sys # para leer argumentos de la terminal
import subprocess # para ejecutar glpsol
import os # para borrar el fichero temporal
import re # para procesar cadenas

def parse_input_file(input_file):
    """lee el fichero de entrada y extrae los datos necesarios"""
    try:
        with open(input_file, 'r') as f:
            # Filtra líneas vacías o que solo tengan espacios
            lines = [line for line in f.readlines() if line.strip()]
        
        # Comprueba si tenemos al menos 4 líneas de datos
        if len(lines) < 4:
            print("Error: El fichero de entrada no tiene las 4 líneas de datos requeridas.", file=sys.stderr)
            sys.exit(1)
        
        # n y m
        nm_vals = re.findall(r'[\d\.]+', lines[0])
        n, m = map(int, nm_vals)
        
        # k_d y k_p
        kp_vals = re.findall(r'[\d\.]+', lines[1])
        k_d, k_p = map(float, kp_vals)
        
        # d_1 ... d_m
        dist_vals = re.findall(r'[\d\.]+', lines[2])
        distances = list(map(float, dist_vals))
        
        # p_1 ... p_m
        pass_vals = re.findall(r'[\d\.]+', lines[3])
        passengers = list(map(int, pass_vals))

        if len(distances) != m or len(passengers) != m:
            print(f"Error: Inconsistencia en los datos. 'm' es {m}, pero se encontraron:", file=sys.stderr)
            print(f" - {len(distances)} distancias", file=sys.stderr)
            print(f" - {len(passengers)} pasajeros", file=sys.stderr)
            sys.exit(1)
            
        return n, m, k_d, k_p, distances, passengers
    
    except Exception as e:
        print("Error: Error leyendo el fichero de entrada", file=sys.stderr)
        sys.exit(1)

def generate_dat_file(dat_file, n, m, k_d, k_p, distances, passengers):
    """genera el fichero .dat con los datos"""
    try:
        with open(dat_file, 'w') as f:
            f.write("data;\n\n")
            
            # sets
            f.write(f"set BUSES := {' '.join([str(i+1) for i in range(m)])};\n")
            f.write(f"set SLOTS := {' '.join([str(j+1) for j in range(n)])};\n\n")
            
            # parámetros
            f.write(f"param k_d := {k_d};\n")
            f.write(f"param k_p := {k_p};\n\n")
            
            # parámetro distances
            f.write("param distances :=\n")
            for i in range(m):
                f.write(f"  {i+1} {distances[i]}\n")
            f.write(";\n\n")
            
            # parámetro passengers
            f.write("param passengers :=\n")
            for i in range(m):
                f.write(f"  {i+1} {passengers[i]}\n")
            f.write(";\n\n")

            f.write("end;\n")

    except Exception as e:
        print("Error: Error escribiendo el fichero de datos", file=sys.stderr)
        sys.exit(1)
        
def run_glpk(model_file, data_file, solution_file):
    """invoca a glpsol para resolver el problema"""

    # Copiar el entorno actual
    env = os.environ.copy()
    # Forzar la local_configuración a 'C' (inglés) para que glpsol
    # escriba "Rows", "Columns", etc., y no "Filas", "Columnas"
    env['LC_ALL'] = 'C'

    try:
        subprocess.run(
            ['glpsol', '-m', model_file, '-d', data_file, '-o', solution_file],
            check=True,
            capture_output=True, # Captura stdout y stderr
            text=True,
            env=env
        )

    except Exception as e:
        print("Error al invocar GLPK", file=sys.stderr)
        sys.exit(1)

def print_solution(solution_file, m):
    """lee el fichero de solución y muestra los resultados"""
    fun_obj = "No encontrado"
    num_rest = "No encontrado"
    num_vars = "No encontrado"
    assignments = []
    unassigned_buses = set(range(1, m + 1)) # creamos un set con todos los buses
    in_columns_section = False # un flag para saber si estamos leyendo variables

    try:
        with open(solution_file, 'r') as f_sol:
            for line in f_sol:
                line = line.strip()

                # buscar datos generales
                if line.startswith("Objective:"):
                    fun_obj = line.split('=')[-1].strip()
                if "Rows" in line and not line.startswith("Column"):
                    num_rest = line.split()[1]
                if "Columns" in line:
                    num_vars = line.split()[1]

                # para encontrar y leer las variables
                if line.startswith("Column instances:"):
                    in_columns_section = True
                    continue
                if line.startswith("---") and in_columns_section:
                    in_columns_section = False
                    continue

                if in_columns_section:
                    parts = line.split()
                    if len(parts) >= 4 and parts[1].startswith('x') and float(parts[3]) > 0.99:
                        var_name = parts[1]
                        indices_str = var_name.replace("x[", "").replace("]", "")
                        bus_str, slot_str = indices_str.split(',')
                        
                        bus = int(bus_str)
                        slot = int(slot_str)
                        
                        assignments.append((bus, slot))
                        
                        if bus in unassigned_buses:
                            unassigned_buses.remove(bus)

    except Exception:
        print("Error: No se encontró el fichero o no se pudo leer", file=sys.stderr)
        sys.exit(1)

    # Imprimir la salida final 
    print(f"Valor óptimo de la función objetivo: {fun_obj}")
    print(f"Número de variables de decisión: {num_vars}")
    print(f"Número de restricciones totales: {num_rest}")

    print("\nAutobuses Asignados a Franjas:")
    if assignments:
        for bus, slot in sorted(assignments):
            print(f"  - Autobús {bus} asignado a la franja {slot}")
    else:
        print("Ningún autobús fue asignado a una franja")
        
    print("\nAutobuses no asignados:")
    if unassigned_buses:
        for bus in sorted(list(unassigned_buses)):
            print(f"  - Autobús {bus} no asignado.")
    else:
        print("Todos los autobuses fueron asignados")

# main
if __name__ == "__main__":
    
    if len(sys.argv) != 3:
        print("Uso: gen-1.py <fichero-entrada> <fichero-salida.dat>", file=sys.stderr)
        sys.exit(1)
        
    input_file = sys.argv[1]
    dat_file = sys.argv[2]
    model_file = "parte-2-1.mod"
    solution_file = "temp_solution.txt" # Fichero temporal

    # 1. Leer entrada
    n, m, k_d, k_p, distances, passengers = parse_input_file(input_file)
    
    # 2. Generar .dat
    generate_dat_file(dat_file, n, m, k_d, k_p, distances, passengers)
    
    # 3. Resolver
    run_glpk(model_file, dat_file, solution_file)
    
    # 4. Mostrar solución
    print_solution(solution_file, m)
    
    # 5. Limpiar
    os.remove(solution_file)
