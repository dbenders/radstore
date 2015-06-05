#!/bin/bash

#recibe como único parámetro los puntos
product_id=`echo $2 | cut -f 2 -d =`
los_puntos=los_puntos.csv
tif=puntos.tif
shp=puntos.shp
csv=puntos.csv
tmp=puntos.tmp
vrt=puntos.vrt
new_shp_name=shp

rm ${los_puntos}
rm -rf ${new_shp_name}
curl -o ${los_puntos} "http://localhost:8080/api/v1/products/${product_id}/content"

dir_base=./

#Prepara el encabezado para el csv
#echo lon,lat,dbz > ${csv}
#cat ${csv}
#dumpea encabezado y datos reemplazando espacios por comas
cat ${csv} ${los_puntos} | sed 's/\s/,/g' > ${tmp}
cat ${tmp} > ${csv}
echo Preparando datos...
#head ${csv}

echo Convirtiendo a shp...
ogr2ogr -f "ESRI Shapefile" ${new_shp_name} ${vrt} -overwrite

echo Crear imagen en blanco...
cp ${dir_base}template-grilla-TM-LIMPIA.tif ${tif}

#Rasterizar los puntos del barrido
echo Rasterizar los puntos del barrido
gdal_rasterize -ts 487 505 -a_nodata -99 -a dbz -l puntos ./${new_shp_name}/${shp}  ${tif}

#Suavizar la imagen
venv/bin/python completa-blancos.py ${tif} 2 max

#Sube 
venv/bin/python upload.py ${product_id}

#cambia de disco los hechos
#mv ${los_puntos} ${dir_hechos}


