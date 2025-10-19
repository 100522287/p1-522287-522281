################################
# SETS
################################

set BUSES; # autobuses (1,...,m)
set SLOTS; # franjas horarias (1,...,n)

################################
# PARAMETROS
################################

param k_d;  # coste en euros por kilómetro
param k_p;  # penalización en euros por pasajero

param distances{i in BUSES};  # distancia del autobús i al taller
param passengers{i in BUSES};  # pasajeros del autobús i

################################
# VARIABLES
################################

var x{i in BUSES, j in SLOTS}, binary; # x=1 si autobús i se asigna a franja j

################################
# F.O.
################################

# minimizar coste de asignados + penalización de no asignados
minimize TOTAL_COST:
    sum{i in BUSES, j in SLOTS} (k_d * distances[i]) * x[i,j] + sum{i in BUSES} (k_p * passengers[i]) * (1 - sum{j in SLOTS} x[i,j]);

################################
# CONSTRAINTS
################################

# cada franja puede ser ocupada por un autobús como máximo 
s.t. slot_capacity{j in SLOTS}:
    sum{i in BUSES} x[i,j] <= 1;

# cada autobús o se asigna a una franja o se deja sin asignar
s.t. bus_assignment{i in BUSES}:
    sum{j in SLOTS} x[i,j] <= 1;

################################
# SOLVE
################################

solve;
end;
