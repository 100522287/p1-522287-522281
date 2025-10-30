################################
# SETS
################################

set BUSES; # autobuses (1,...,m)
set SLOTS; # franjas horarias (1,...,n)
set WORKSHOPS; # talleres (1,...,u)

################################
# PARAMETROS
################################

# conflictos entre autobuses i y l (pasajeros compartidos)
param c{i in BUSES, l in BUSES};

# disponibilidad de franja k en taller j (0 o 1)
# CORREGIDO: Invertido el orden de los índices a [SLOTS, WORKSHOPS] (n x u)
param o{k in SLOTS, j in WORKSHOPS};

################################
# VARIABLES
################################

# x=1 si autobús i se asigna al taller j en la franja k
var x{i in BUSES, j in WORKSHOPS, k in SLOTS}, binary;

# y=1 si autobuses i y l están ambos en la franja k (en talleres diferentes)
var y{i in BUSES, l in BUSES, k in SLOTS: i < l}, binary;

################################
# F.O.
################################

# minimizar el número total de usuarios asignados a la misma franja en talleres diferentes
minimize TOTAL_CONFLICTS:
    sum{i in BUSES, l in BUSES, k in SLOTS: i < l} c[i,l] * y[i,l,k];

################################
# CONSTRAINTS
################################

# Restricción 1: Todos los autobuses deben ser asignados a una franja (y solo una) de algún taller
s.t. bus_assignment{i in BUSES}:
    sum{j in WORKSHOPS, k in SLOTS} x[i,j,k] = 1;

# Restricción 2: Cada franja de cada taller solo puede ser ocupada por un autobús como máximo
# y solo si está disponible (o[k,j] = 1)
# CORREGIDO: Invertido el orden de iteración y el acceso a 'o'
s.t. slot_capacity{k in SLOTS, j in WORKSHOPS}:
    sum{i in BUSES} x[i,j,k] <= o[k,j];

# Restricción 3a: y[i,l,k] solo puede valer 1 si el autobús i está en la franja k
s.t. conflict_bus_i{i in BUSES, l in BUSES, k in SLOTS: i < l}:
    y[i,l,k] <= sum{j in WORKSHOPS} x[i,j,k];

# Restricción 3b: y[i,l,k] solo puede valer 1 si el autobús l está en la franja k
s.t. conflict_bus_l{i in BUSES, l in BUSES, k in SLOTS: i < l}:
    y[i,l,k] <= sum{j in WORKSHOPS} x[l,j,k];

# Restricción 3c: y[i,l,k] debe ser 1 si ambos autobuses i y l están en la franja k
# (esto detecta el conflicto independientemente del taller)
s.t. conflict_both{i in BUSES, l in BUSES, k in SLOTS: i < l}:
    y[i,l,k] >= sum{j in WORKSHOPS} x[i,j,k] + sum{j in WORKSHOPS} x[l,j,k] - 1;

################################
# SOLVE
################################

solve;
end;