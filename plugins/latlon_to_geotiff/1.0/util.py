import requests
import simplejson
import datetime
import radstore_client
import os

radstore_client.config.base_url = os.environ.get('RADSTORE_API_URL','http://127.0.0.1:3003/api/v1')

def exists(id):
	prod = radstore_client.Product.get(id)
	name = '%s.tif' % prod.name.split('.')[0]
	return radstore_client.Product.query().filter(name=name).count() > 0

def upload(id,fname):
	prod = radstore_client.Product.get(id)

	transf = radstore_client.Transformation()
	transf.datetime = datetime.datetime.now()
	transf.process = 'latlon_to_geotiff'
	transf.add_input(prod)

	output = prod.copy()
	output.type = 'geotiff.original'
	output.name = '%s.tif' % prod.name.split('.')[0]
	output.save()

	output.content = open(fname).read()
	output.save_content()

	transf.add_output(output)

	transf.save()


import sys
def main():
	cmd = sys.argv[1]
	if cmd == "exists":
		sys.exit(1 if exists(sys.argv[2]) else 0)

	elif cmd == "upload":
		print "uploading..."
		upload(sys.argv[2],sys.argv[3])
		print "done."

if __name__ == '__main__':
	main()
