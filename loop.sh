#!/bin/bash
#Lee un archivo CSV (campos separados por coma sin cabecera) que se le entrega por argumento y llama a la generación de las facturas
#la estructura del archivo CSV es: ID contacto,RUT(dni),NombreCompleto,zona(sector),cantidadDeMesesDeDeuda
line=$1
IFS=',' read -r -a array <<< "$line"
partner_id=${array[0]}
sector=${array[3]}
debts=${array[4]}
date=$(date -d "Jan 1 2024" +%Y-%m-%d)
#realiza la ejecución dependiendo la cantidad de meses de deuda
for(( i = 1; i <= $debts; i++ )) 
do
        python3 generateInvoice.py $partner_id "$sector" $date
        #mueve la fecha de generación un mes atrás por cada ciclo
        date=`date -d "$(date +%Y-%m-1) -$i month" +%Y-%m-%d`
done