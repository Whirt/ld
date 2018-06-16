#/bin/bash

# Alternativa artigianale a usare crontab
# il difetto di crontb è che è legato alla path
# del sistema, in tal caso spostando il progetto in altri
# sistemi richiede un minimo di modifica alle path,
# cosa che si vuole evitare

source ../env/bin/activate;

while true; do 
		python manage.py runcrons ; 
		sleep 60; 
done
