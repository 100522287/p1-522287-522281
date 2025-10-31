################################
# SETS
################################

set BUSES; # Autobuses
set SLOTS; # Franjas
set WORKSHOP; # Talleres

################################
# PARAMETROS
################################

# Numero de pasajeros que han contratado simultaneamente los servicios de los autobuses
param c {BUSES,BUSES} >= 0;

# Indica si la franja s esta disponible en el taller t
param o {SLOTS,WORKSHOP} binary;

################################
# VARIABLES
################################

# x[i,s,t] = 1 si el autobus i usa la franja s en el taller t
var x {i in BUSES, s in SLOTS, t in WORKSHOP} binary;

# y[i,j,s] = 1 si (i y j) usan la misma franja s (solo se define para i<j para evitar doble conteo)
var y {i in BUSES, j in BUSES, s in SLOTS: i < j} binary;

################################
# F.O.
################################

# 4. Objetivo: minimizar conflictos de clientes
#    Tres sumatorios con i<j para no duplicar pares (i,j) y (j,i)
minimize Impacto:
  sum {s in SLOTS, i in BUSES, j in BUSES: i < j} c[i,j] * y[i,j,s];

################################
# CONSTRAINTS
################################

# 1. Restriccion: cada autobus se asigna exactamente a una pareja (franja, taller)
s.t. Asignacion {i in BUSES}:
  sum {s in SLOTS, t in WORKSHOP} x[i,s,t] = 1;

# 2. Restriccion: capacidad/disponibilidad por (franja, taller)
s.t. Capacidad {s in SLOTS, t in WORKSHOP}:
  sum {i in BUSES} x[i,s,t] <= o[s,t];

# 3. Restriccion  AND: y[i,j,s] = 1 si (i usa s) Y (j usa s), solo para i < j
s.t. And1 {i in BUSES, j in BUSES, s in SLOTS: i < j}:
  y[i,j,s] <= sum {t in WORKSHOP} x[i,s,t];

s.t. And2 {i in BUSES, j in BUSES, s in SLOTS: i < j}:
  y[i,j,s] <= sum {t in WORKSHOP} x[j,s,t];

s.t. And3 {i in BUSES, j in BUSES, s in SLOTS: i < j}:
  y[i,j,s] >= sum {t in WORKSHOP} x[i,s,t] + sum {t in WORKSHOP} x[j,s,t] - 1;

################################
# SOLVE
################################

solve;
end;