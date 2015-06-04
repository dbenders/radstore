#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Completa-Blancos.py
#       
#       Autores: Santiago Banchero, Yanina Bellini Saibene
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#       
#       

try:
	from osgeo import gdal
	from osgeo import osr 
except ImportError:
	raise ImportError,"Se requiere el modulo osgeo.  Se puede descargar de http://www.lfd.uci.edu/~gohlke/pythonlibs/"

try:
	import numpy as np, numpy.ma as ma  
except ImportError:
	raise ImportError,"Se requiere el modulo numpy. http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy"

from sys import argv   #Todo: change this for argparse, this include how to use
import copy

nodata = -99.0 #Todo: no hardcode for nan data, a parameter maybe ?

def get_celdas(f,c):
	if f == 0 and c == 0:
		return [(f,c+1),(f+1,c),(f+1,c+1)]
	elif f == 0:
		return [(f,c-1),(f,c+1),(f+1,c-1),(f+1,c),(f+1,c+1)]
	elif c == 0:
		return [(f-1,c),(f-1,c+1),(f,c+1),(f+1,c),(f+1,c+1)]
	else:
		return [(f-1,c-1),(f-1,c),(f-1,c+1),(f,c-1),(f,c+1),(f+1,c-1),(f+1,c),(f+1,c+1)]
		
	
def rellenar(mtx1, criterio):
	mtx2 = copy.copy(mtx1)
	fila,col = mtx1.shape
	vecinos = []
	aux = list(mtx1)
	for f in range(fila):
		for c in range(col):
			if mtx1[f,c] == nodata:
				celdas = get_celdas(f,c)
				for fc in celdas:
					x,y = fc
					try:
						vecinos.append(aux[x][y])
					except:
						pass
				vecinos_tmp = np.array(vecinos)
				try:
					mtx2[f,c] = eval('vecinos_tmp[vecinos_tmp <> nodata].'+criterio+'()') #eval('max(x)') #max(vecinos)
				except ValueError,e:
					mtx2[f,c] = nodata
				vecinos = []
	return mtx2
	

def main():
	path_file = argv[1]
	iteraciones = int(argv[2])
	criterio = argv[3]
	print """Corriendo: completa-blancos
Raster: %s
Iteraciones: %s
Criterio: %s
NoData: %f"""%(path_file, iteraciones, criterio,nodata)
	print "Leyendo imagen ...",
	raster = gdal.Open(path_file, gdal.GA_Update)
	print "Ok!"
	mtx = raster.GetRasterBand(1).ReadAsArray()
	print "Rellenando ...",
	for i in range(iteraciones):
		mtx = rellenar(mtx, criterio)
	raster.GetRasterBand(1).WriteArray(mtx)
	print "Ok!"
	raster = None
	return 0

if __name__ == '__main__':
	main()

