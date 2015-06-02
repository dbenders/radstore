import pymongo
import xmltodict
import pymongo
import gridfs
import base64
import zlib
import re
import simplejson
import dateutil.parser
import datetime
import os
import requests

client = pymongo.MongoClient()
db = client['radar']

def process_blob(blob):
	return zlib.decompress(blob[4:])

def process_metadata(val):
	if isinstance(val,dict):
		return dict((k.replace('@',''),process_metadata(v))
			for k,v in val.iteritems())

	elif isinstance(val,list):
		return map(process_metadata, val)

	elif isinstance(val,tuple):
		return tuple(map(process_metadata, val))

	elif isinstance(val,basestring):
		val = val.strip()
		if len(val) == 0: return val

		l = val.lower()
		if l == 'on': return True
		elif l == 'off': return False
		elif l == 'none': return None

		try: return float(val)
		except: pass
		try: return int(val)
		except: pass
		try: 
			if 'T' in val: return dateutil.parser.parse(val)
		except: pass

		try: return map(float, val.split())
		except: pass
		try: return map(int, val.split())
		except: pass

	return val


def upload(fname):
	with open(fname) as f:
		t = ''
		for line in f:
			if line == '<!-- END XML -->\n': break
			t += line
		data = xmltodict.parse(t)
		data = process_metadata(data)

		doc = {
			'name': os.path.split(fname)[-1],
			'type': 'vol',
			'datetime': data['volume']['datetime'],
			'variable': data['volume']['scan']['slice'][0]['slicedata']['rawdata']['type'],
			#'metadata': data['volume']
		}
		# print simplejson.dumps(data, indent=3, default=lambda x:str(x))
		# asdffdsa

		#result = db['product'].insert_one(doc)
		resp = requests.post('http://localhost:8080/api/v1/products', 
			headers={'Content-Type':'application/json'}, data=simplejson.dumps(doc, default=str))

		data = simplejson.loads(resp.text)

		id = data['data']['product']['_id']
		requests.post('http://localhost:8080/api/v1/products/%s/content' % id, data=open(fname).read())

		# blob = None
		# blobdata = None
		# for line in f:
		# 	if blobdata is None:
		# 		if line.startswith('<BLOB'):
		# 			blobdata = ''
		# 			blob = xmltodict.parse(line+'</BLOB>')
		# 	else:
		# 		if line == '</BLOB>\n':
		# 			d = {
		# 				'datetime': data['volume']['@datetime'],
		# 				'type': data['volume']['scan']['slice'][0]['slicedata']['rawdata']['@type'],
		# 				'blobid': blob['BLOB']['@blobid']
		# 			}
		# 			blobfile = fs.new_file(**d)
		# 			blobfile.write(process_blob(blobdata))
		# 			blobfile.close()
		# 			blobdata = None
		# 		else:
		# 			blobdata += line
		
import sys
def main():
	

	# clean all 
	client.drop_database('radar')
	os.system('rm fs/*')
	#db['product'].create_index([('id',pymongo.ASCENDING)],unique=True)

	for fname in sys.argv[1:]:
		print fname
		upload(fname)

if __name__ == '__main__':
	main()