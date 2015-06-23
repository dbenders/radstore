#!/bin/bash

#recibe como único parámetro los puntos

product_id=$1
tmpdir=/tmp/latlon_to_geotiff/${product_id}
uuid=${product_id} #$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
#tmpfile=${tmpdir}/${uuid}

tsv=${tmpdir}/puntos.tsv
csv=${tmpdir}/puntos.csv
shp=${tmpdir}/puntos_shp
tif=${tmpdir}/puntos.tif

vrt=${tmpdir}/puntos.vrt

api_url='http://127.0.0.1:3003/api/v1'


# new_shp_name=${UUID}.shp
# los_puntos=${UUID}.sv
# tif=${UUID}.tif
# shp=puntos.shp
# csv=${UUID}.csv
# tmp=${UUID}.tmp

mkdir -p /tmp/latlon_to_geotiff
rm -rf ${tmpdir}
mkdir -p ${tmpdir}

echo Chequeando si existe...
venv/bin/python util.py exists ${product_id}
if [ $? -eq 1 ]; then
	echo Ya existe, saliendo.
	exit
fi

echo Descargando...
curl -o ${tsv} "${api_url}/products/${product_id}/content"

echo Preparando datos...
cat ${tsv} | sed 's/\s/,/g' > ${csv}
cp ./puntos.vrt ${vrt}
  
echo Convirtiendo a shp...
(cd ${tmpdir}; ogr2ogr -f "ESRI Shapefile" ${shp} ${vrt})

echo Crear imagen en blanco...
cp ./template-grilla-TM-LIMPIA.tif ${tif}

#Rasterizar los puntos del barrido
echo Rasterizar los puntos del barrido...
gdal_rasterize -ts 487 505 -a_nodata -99 -a dbz -l puntos ${shp}/puntos.shp  ${tif}

#Suavizar la imagen
venv/bin/python completa-blancos.py ${tif} 2 max

#Sube 
echo Subiendo ${product_id}...
venv/bin/python util.py upload ${product_id} ${tif}

#borra
rm -rf ${tmpdir}

#cambia de disco los hechos
#mv ${los_puntos} ${dir_hechos}


