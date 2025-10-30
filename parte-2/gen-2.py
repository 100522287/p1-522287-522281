import sys
import subprocess
import os
import re

def parse_input_file(input_file):
    """lee el fichero de entrada y extrae los datos necesarios"""
    try:
        with open(input_file, 'r') as f:
            lines = [line for line in f.readlines() if line.strip()]
        
        if len(lines) < 2:
            print("Error: El fichero de entrada no tiene suficientes líneas de datos.", file=sys.stderr)
            sys.exit(1)
        
        # n, m, u
        first_vals = re.findall(r'[\d\.]+', lines[0])
        n, m, u = map(int, first_vals)
        
        # matriz c (m x m)
        c_matrix = []
        for i in range(1, m + 1):
            if i >= len(lines):
                print(f"Error: Falta la línea {i} de la matriz c.", file=sys.stderr)
                sys.exit(1)
            row_vals = re.findall(r'[\d\.]+', lines[i])
            c_matrix.append(list(map(int, row_vals)))
        
        # matriz o (u x n)
        o_matrix = []
        for j in range(m + 1, m + 1 + n):
            if j >= len(lines):
                print(f"Error: Falta la línea {j} de la matriz o.", file=sys.stderr)
                sys.exit(1)
            row_vals = re.findall(r'[\d\.]+', lines[j])
            o_matrix.append(list(map(int, row_vals)))
        
        # validación
        if len(c_matrix) != m or any(len(row) != m for row in c_matrix):
            print(f"Error: La matriz c debe ser {m}x{m}.", file=sys.stderr)
            sys.exit(1)
            
        if len(o_matrix) != n or any(len(row) != u for row in o_matrix):
            print(f"Error: La matriz o debe ser {n}x{u}.", file=sys.stderr)
            sys.exit(1)
            
        return n, m, u, c_matrix, o_matrix
    
    except Exception as e:
        print(f"Error: Error leyendo el fichero de entrada: {e}", file=sys.stderr)
        sys.exit(1)

def generate_dat_file(dat_file, n, m, u, c_matrix, o_matrix):
    """genera el fichero .dat con los datos"""
    try:
        with open(dat_file, 'w') as f:
            f.write("data;\n\n")
            
            # sets
            f.write(f"set BUSES := {' '.join([str(i+1) for i in range(m)])};\n")
            f.write(f"set SLOTS := {' '.join([str(j+1) for j in range(n)])};\n")
            f.write(f"set WORKSHOPS := {' '.join([str(k+1) for k in range(u)])};\n\n")
            
            # parámetro c (matriz de conflictos)
            f.write("param c :\n")
            f.write("     " + " ".join([f"{j+1:4}" for j in range(m)]) + " :=\n")
            for i in range(m):
                f.write(f"  {i+1:2} " + " ".join([f"{c_matrix[i][j]:4}" for j in range(m)]) + "\n")
            f.write(";\n\n")
            
            # parámetro o (disponibilidad de franjas)
            f.write("param o :\n")
            f.write(" " + " ".join([f"{k+1:3}" for k in range(u)]) + " :=\n")
            for j in range(n):
                f.write(f" {j+1:2} " + " ".join([f"{o_matrix[j][k]:3}" for k in range(u)]) + "\n")
            f.write(";\n\n")

            f.write("end;\n")

    except Exception as e:
        print(f"Error: Error escribiendo el fichero de datos: {e}", file=sys.stderr)
        sys.exit(1)

def run_glpk(model_file, data_file, solution_file):
    """invoca a glpsol para resolver el problema"""
    env = os.environ.copy()
    env['LC_ALL'] = 'C'
    try:
        subprocess.run(
            ['glpsol', '-m', model_file, '-d', data_file, '-o', solution_file],
            check=True,
            capture_output=True,
            text=True,
            env=env
        )
    except Exception as e:
        print(f"Error al invocar GLPK: {e}", file=sys.stderr)
        sys.exit(1)

def print_solution(solution_file):
    """lee el fichero de solución y muestra los resultados"""
    fun_obj = "No encontrado"
    num_rest = "No encontrado"
    num_vars = "No encontrado"
    assignments = []
    in_columns_section = False

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

                # para encontrar y leer las variables x
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
                        indices = indices_str.split(',')
                        
                        bus = int(indices[0])
                        workshop = int(indices[1])
                        slot = int(indices[2])
                        
                        assignments.append((bus, workshop, slot))

    except Exception as e:
        print(f"Error: No se encontró el fichero o no se pudo leer: {e}", file=sys.stderr)
        sys.exit(1)

    # Imprimir la salida final
    print(f"Valor óptimo de la función objetivo: {fun_obj}")
    print(f"Número de variables de decisión: {num_vars}")
    print(f"Número de restricciones totales: {num_rest}")

    print("\nAsignaciones de Autobuses:")
    if assignments:
        for bus, workshop, slot in sorted(assignments):
            print(f"  - Autobús {bus} asignado al taller {workshop} en la franja {slot}")
    else:
        print("No se encontraron asignaciones")

# main
if __name__ == "__main__":
    
    if len(sys.argv) != 3:
        print("Uso: gen-2.py <fichero-entrada> <fichero-salida.dat>", file=sys.stderr)
        sys.exit(1)
        
    input_file = sys.argv[1]
    dat_file = sys.argv[2]
    model_file = "parte-2-2.mod"
    solution_file = "temp_solution_2.txt"

    # 1. Leer entrada
    n, m, u, c_matrix, o_matrix = parse_input_file(input_file)
    
    # 2. Generar .dat
    generate_dat_file(dat_file, n, m, u, c_matrix, o_matrix)
    
    # 3. Resolver
    run_glpk(model_file, dat_file, solution_file)
    
    # 4. Mostrar solución
    print_solution(solution_file)
    
    # 5. Limpiar
    os.remove(solution_file)