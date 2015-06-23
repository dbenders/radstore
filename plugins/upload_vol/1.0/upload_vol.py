import pymongo
import xmltodict
import pymongo
#import gridfs
import base64
import zlib
import re
import simplejson
import dateutil.parser
import datetime
import os
import glob
import radstore_client

radstore_client.config.base_url = os.environ.get('RADSTORE_API_URL','http://127.0.0.1:3003/api/v1')


def process_blob(blob):
	return zlib.decompress(blob[4:])

def process_metadata(val):
	if isinstance(val,dict):
		return dict((k.replace('@',''),process_metadata(v)) for k,v in val.iteritems())

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
	print fname
	with open(fname) as f:
		t = ''
		for line in f:
			if line == '<!-- END XML -->\n': break
			t += line
		data = xmltodict.parse(t)
		data = process_metadata(data)

		if radstore_client.Product.query().filter(type='vol',name=os.path.split(fname)[-1]).count() > 0:
			print "\tEXISTS"
			return

		prod = radstore_client.Product()
		prod.name = os.path.split(fname)[-1]
		prod.type = 'vol'
		prod.datetime = data['volume']['datetime']
		prod.variable = data['volume']['scan']['slice'][0]['slicedata']['rawdata']['type']

		prod.save()

		prod.content = open(fname).read()
		prod.save_content()

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
	cmd, args = radstore_client.parse_cmdline(sys.argv)
	# clean all 
	#os.system('rm fs/*')

	if cmd == "import_file":
		upload(args['file'])
	elif cmd == "import_dir":		
		pattern = os.path.join(args['dir'],args.get('pattern',''))
		for fname in glob.glob(pattern):
			try:
				upload(fname)
			except Exception,e:
				print "ERROR: %s" % e
	else:
		print "ERROR: Invalid command: %s" % cmd

if __name__ == '__main__':
	main()
