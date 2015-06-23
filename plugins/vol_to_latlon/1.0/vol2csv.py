# -*- encoding: utf8
# Autores: Banchero, Santiago; Bellini Saibene Yanina
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
#       Este script es parte de la Tesis: 
#         “Estimación de ocurrencia de granizo en superficie y daño en cultivos 
#			mediante datos del radar meteorológico utilizando técnicas de data mining”.
#
#		correspondiente a la maestría en DM&KD de la Universidad Austral
#		Aspirante: Yanina Noemí Bellini Saibene
#

import struct
import sys
from math import log10
import zlib
# try:
# 	from PyQt4 import QtCore
# except ImportError:
# 	raise ImportError,"Se requiere el modulo PyQt4.  Se puede descargar de http://www.riverbankcomputing.co.uk/software/pyqt/download"
try:
	from lxml import etree
except ImportError:
	raise ImportError,"Se requiere el modulo lxml. Se puede descargar de http://www.lfd.uci.edu/~gohlke/pythonlibs/"	
try:
	from numpy import array,nan,isfinite,zeros,float,sin,cos,pi,mgrid
except ImportError:
	raise ImportError,"Se requiere el modulo numpy. Se puede descargar de http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy"	

# Todo: Estos valores son los correspondientes a Anguil, en los .vol esta información está en radarinfo.  
# se podría ver de tomar los datos directamente desde alli y asi hacerlo genérico para cualquier radar
# Todo: These values are from Anguil radar. Inside .vol we can find this information, we will take this data from there.
lon = -63.990067
lat= -36.539683

#Todo: estos datos corresponden para el rango de 240 km, deberiamos generalizarlo para el de 120 y 480.
# These data correspond to the range of 240 km, we should generalize to the 120 and 480.
azimth = 360
bins = 480
rango=240
binres=0.5
R=12742/2; # Radio medio de la Tierra
m=2*pi*R/360
tipoArchivo=''

#Función que devuelve el encabezado del volumen
#Return the volume head
def get_header_vol(fh=None):
    try:
		linea = fh.next()
		xml = ''
		while linea:
			if linea.startswith('</volume>'):
				xml += linea
				break
			xml += linea
			linea = fh.next()
		return xml
    except StopIteration:
		raise StopIteration,"El archivo que se intenta abrir no contiene datos"	   
    

#Función que devuelve los Blobs con los datos del volumen
# Returns the Blobs with the actual radar data
def get_blobs(fh=None):
    linea = fh.next()
    blobs = []
    bindata = ''
    while linea:
        #Si la linea empieza con <blob
        if linea.startswith('<BLOB blobi'):
            linea = fh.next()
            while linea:
                if linea.startswith('</BLOB>'):
                    blobs.append(bindata)
                    bindata = ''
                    break
                bindata += linea
                try:
				    linea = fh.next()
                except StopIteration,e:
				    linea = None
        try:
            linea = fh.next()
        except StopIteration,e:
            linea = None
            
    return blobs

#Función que imprime la información del RADAR, extraido de la informacion contenida en el volumen.
#Print the RADAR information in the volume scan
def print_radarinfo(ri):
    name,wavelen,beamwidth = ri.getchildren()
    print """NOMBRE:    %s
WAVELEN:   %s
BEAMWIDTH: %s""" %(name.text,wavelen.text,beamwidth.text)


def print_slice(lst_slice):
    
    for sl in lst_slice:
        slice = sl.getchildren()
        for ele in slice:
            if ele.tag == 'slicedata':
                rayinfo,rawdata = ele.getchildren()
                print """Rays: %s Min: %s Max: %s BlobID: %s Depth: %s Type: %s Bins: %s """ %(rawdata.attrib['rays'],rawdata.attrib['min'],rawdata.attrib['max'],rawdata.attrib['blobid'],rawdata.attrib['depth'],rawdata.attrib['type'],rawdata.attrib['bins'])
    return rawdata.attrib['type']

#Función que realiza el cálculo del valor real de cada variable.
#Function that calculates the actual value of each variable.
def get_depth(depth, variable):
    if variable=='ZDR':
		db_min = -8.0
		db_max = 12.0
		dmi = 1.0
		dma = 255.0
		parametro=3
    if variable=='dBZ':
		db_min = -31.5
		db_max = 95.5
		dmi = 1.0
		dma = 255.0
		parametro= 1
    if variable=='PhiDP':
		db_min = 0.0
		db_max = 360.0
		dmi = 1.0   #digital number
		dma = 65535.0 #digital number
		parametro=3
    if variable=='KDP':
		db_min = -20.0
		db_max = 20.0
		dmi = 1.0   #digital number
		dma = 65535.0 #digital number
		parametro=3
    if variable=='RhoHV':
		db_min = 0.0
		db_max = 1.0
		dmi = 1.0   #digital number
		dma = 255.0 #digital number
		parametro= 3
    return round(((float(depth) - dmi)/(dma - dmi))*(db_max - (db_min)) + db_min,parametro)


#Función que obtiene la matriz de datos reales del volumen procesado
#Get the matrix of real data processed volume
def get_matriz_vol(d,tipoArchivo):
    inicio = 0
    blob = zeros((azimth,bins),dtype=float)
    for az in range(azimth):
        
        #un_bin = d.data()[inicio:inicio + bins]
        un_bin = d[inicio:inicio + bins]

        inicio += bins
        #recorro un_bin obviando el primer byte que es el separador
        for i,b in enumerate(un_bin):
            ndepth = struct.unpack_from('B',b)

            if ndepth[0] == 0:
                blob[az][i] = -99.0
                
            elif ndepth[0] > 0:
				
				blob[az][i] = get_depth(ndepth[0], tipoArchivo)
               
    return blob #[::-1,:]

def get_matriz_vol_16b(d, tipoArchivo):
    inicio = 0
    
    bytes = 2 # resolucion de la imagen 16 bits = 2 bytes
    
    blob = zeros((azimth,bins),dtype=float)
    for az in range(azimth):
        
        #un_bin = d.data()[inicio:inicio + bins*bytes]
        un_bin = d[inicio:inicio + bins*bytes]

        #genero una lista de los 2 bytes y reverseados...jejeje
        un_bin = [un_bin[i:i+bytes][::-1] for i in range(0, len(un_bin), bytes)]
        
        inicio += bins*bytes
        #recorro un_bin obviando el primer byte que es el separador
        for i,b in enumerate(un_bin):
            ndepth = struct.unpack_from('H',b)

            if ndepth[0] == 0:
                blob[az][i] = -99.0

            elif ndepth[0] > 0:
                blob[az][i] = get_depth(ndepth[0], tipoArchivo)
               
               
    return blob #--[::-1,:]


def get_angulos(d):
    inicio = 0
    bytes = 2
    
    db_min = 0.0
    db_max = 359.995
    dmi = 0.0
    dma = 65535.0
    
    grados = []
    startangle = None
    for az in range(len(d)):
        #un_bin = d.data()[inicio:inicio + bytes][::-1]
        un_bin = d[inicio:inicio + bytes][::-1]

        inicio += bytes
        if len(un_bin) == 2:
            angulo = struct.unpack_from('H',un_bin)
            if len(grados) == 0:
                startangle = round(((float(angulo[0]) - dmi)/(dma - dmi))*(db_max - (db_min)) + db_min,3)
            grados.append(round(((float(angulo[0]) - dmi)/(dma - dmi))*(db_max - (db_min)) + db_min,3))
            #print round(((float(angulo[0]) - dmi)/(dma - dmi))*(db_max - (db_min)) + db_min,3)
    return startangle,grados


import urllib
import requests
import simplejson
import datetime
import radstore_client
import os
from StringIO import StringIO

radstore_client.config.base_url = os.environ.get('RADSTORE_API_URL','http://127.0.0.1:3003/api/v1')

def convert(prod):    
  
    f = StringIO(prod.content)
    xml_header = get_header_vol(f)
    blobs = get_blobs(f)

    vol = etree.fromstring(xml_header)
    root = vol.getroottree().getroot()
    
    #Algunos volumenes vienen con mas información, agregan el nodo history, para eso hacemos el control de errores.
    try:
		scan, radarinfo = root.getchildren()
    except ValueError:
		scan, radarinfo, history = root.getchildren()
		
    print_radarinfo(radarinfo)
    slice = scan.findall('slice')
    tipoArchivo= print_slice(slice)
    print 'Tipo Archivo:'+tipoArchivo
    print 'BLOBS: %i' % len(blobs)
    bandas = []
    grados = []

    transf = radstore_client.Transformation()
    transf.datetime = datetime.datetime.now()
    transf.process = 'vol2latlon'
    transf.add_input(prod)
    
    for i,bl in enumerate(blobs):

        #up=QtCore.qUncompress(bl)
        up=zlib.decompress(bl[4:])
        
        if i % 2 == 0:
            print 'Blob',i,len(up) - bins,azimth*bins,len(up) - bins==azimth*bins
            startangle, grados = get_angulos(up)
               
        if i % 2 <> 0:
            print 'Blob',i,len(up) - bins,azimth*bins,len(up) - bins==azimth*bins
            if tipoArchivo in ['KDP','PhiDP']:
				blobs_img = get_matriz_vol_16b(up, tipoArchivo)
            else:
				blobs_img = get_matriz_vol(up, tipoArchivo)
		            
            
            #TODO: de acuerdo a lo indicado por el usuario convertir a geográficas y guardar
            #o dejar el polares y guardar.

            if radstore_client.Product.query().filter(
                type='csv.latlon', datetime=prod.datetime, variable=prod.variable, slice=i).count() > 1:
                    print "exists"
                    continue

            outp = prod.copy()
            outp.type = 'csv.latlon'
            outp.name = '%s_%i.csv' % (prod.name.split('.')[0], i)
            outp.slice = i
            outp.save()

            data = 'lon lat dbz\n'
            
            aux_a = blobs_img[:round(360 - startangle)]
            aux_b = blobs_img[round(360 - startangle):]
            blobs_img = array(list(aux_b)+list(aux_a))
            
            points = []
            values = []
            
            for ray in grados:
                for bi in range(bins):
                    y = lat + ((bi*0.5)/m) * cos((ray)*pi/180)
                    x = lon + ((bi*0.5)/m) * sin((ray)*pi/180)/cos( y * pi/180)
                                            
                    points.append([x,y])
                    #fo.write("%f %f %f\n" %(x,y,blobs_img[ray][bi]))
                    data += "%f %f %f\n" %(x,y,blobs_img[ray][bi])
                    values.append(blobs_img[ray][bi])

            outp.content = data
            outp.save_content()
            transf.add_output(outp)

    transf.save()        

import sys
def main():
    cmd, args = radstore_client.parse_cmdline(sys.argv)
    if cmd == 'to_latlon':
        print "to_latlon %s" % args['source']
        prod = radstore_client.Product.get(args['source'])
        convert(prod)
    elif cmd == 'to_latlon_multiple':
        q = json.loads(params['query'])
        for prod in radstore_client.Product.query().filter(type='vol', **q).all():
            print "to_latlon %s" % prod._id
            convert(prod)

# Cuerpo principal del Script
if __name__ == '__main__':
    main()
