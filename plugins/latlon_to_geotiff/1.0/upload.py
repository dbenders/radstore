import requests
import simplejson
import datetime


api_url = 'http://127.0.0.1:3003/api/v1'

def check_result(resp):
	if not resp.ok:
		print "ERROR: %d: %s" % (resp.status_code, resp.reason)
		print resp.text
		assert False

	resp_data = simplejson.loads(resp.text)
	if resp_data['status'] != 'ok':
		print "ERROR: %s" % resp_data['message']
		assert False
	return resp_data


def upload(id,fname):
	src = check_result(
		requests.get('%s/products/%s' % (api_url,id)))['data']['product']

	transformation_metadata = {
		'datetime': datetime.datetime.now(),
		'process': 'latlon_to_geotiff',
		'inputs': [{'_id':src['_id']}]
	}
	trans_data = check_result(
		requests.post('%s/transformations' % api_url, 
		 data=simplejson.dumps(transformation_metadata, default=str)))

	transformation_id = trans_data['data']['transformation']['_id']

	output_metadata = {
		'type': 'geotiff.original',
		'datetime': src['datetime'],
		'variable': src['variable'],
		'name': '%s.tif' % src['name'].split('.')[0],
		'slice': src['slice']
	}

	resp_data = check_result(
		requests.post('%s/transformations/%s/outputs' % (api_url,transformation_id),
			data=simplejson.dumps(output_metadata,default=str)))

	output_id = resp_data['data']['product']['_id']

	data = open(fname).read()
	resp_data = check_result(
		requests.post('%s/products/%s/content' % (api_url,output_id), data=data))


import sys
def main():
	print "uploading..."
	upload(sys.argv[1],sys.argv[2])
	print "done."

if __name__ == '__main__':
	main()
