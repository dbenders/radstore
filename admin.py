import subprocess
import yaml
import pymongo

client = pymongo.MongoClient()
db = client['radar']

def import_plugins():
	print "Importing plugins"
	p = subprocess.Popen(['find','plugins','-name','plugin_info.yaml'],stdout=subprocess.PIPE)
	line = p.stdout.readline().strip()
	while len(line)>0:
		print line
		data = yaml.load(open(line))

		doc = {'$set': data['plugin']}
		
		for transformation in data.get('transformations',[]):
			doc['$addToSet'] = {'transformations':transformation}
		db['plugin'].update_one({'name':data['plugin']['name']},doc,upsert=True)

		for product_type in data.get('product_types',[]):
			db['product_type'].update_one({'name':product_type['name']},{'$set':product_type}, upsert=True)
		line = p.stdout.readline().strip()
	print "done."

def print_usage():
	print "usage: python admin.py <command>"
	print "where command is:"
	print "\timport_plugins"
	print ""

import sys
def main():
	if len(sys.argv) < 2: 
		print_usage()
		return

	cmd = sys.argv[1]
	if cmd == 'import_plugins':
		import_plugins()

if __name__ == '__main__':
	main()