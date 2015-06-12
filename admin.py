import subprocess
import yaml
import pymongo
import os
import subprocess


client = pymongo.MongoClient()
db = client['radar']

def import_plugins():
	print "Importing plugins"
	p = subprocess.Popen(['find','plugins','-name','plugin_info.yaml'],stdout=subprocess.PIPE)
	line = p.stdout.readline().strip()
	while len(line)>0:
		print line
		data = yaml.load(open(line))
		data['plugin']['working_dir'] = os.path.split(line)[0]
		doc = {'$set': data['plugin']}
		
		for transformation in data.get('transformations',[]):
			if doc.get('$addToSet',{}).get('transformations') is not None:
				doc['$addToSet']['transformations']['$each'].append(transformation)
			else:
 				doc['$addToSet'] = {'transformations':{'$each': [transformation]}}
		db['plugin'].update_one({'name':data['plugin']['name']},doc,upsert=True)

		for product_type in data.get('product_types',[]):
			db['product_type'].update_one({'name':product_type['name']},{'$set':product_type}, upsert=True)
		line = p.stdout.readline().strip()
	print "done."

def list_plugins():
	print "Plugins available:"
	for doc in db['plugin'].find():
		print "\t%s" % doc['name']
		for transf in doc['transformations']:
			ln = transf['name']
			if len(transf.get('inputs',[])) > 0:
				ln += " " + " ".join("[%s=...]" % k['name'] for k in transf['inputs'])
			print "\t\t%s" % ln
	print ""

def execute_plugin(plugin_name, transf_name, **kwargs):
	plugin = db['plugin'].find_one({'name':plugin_name})
	if plugin is None:
		print  "plugin '%s' not found" % plugin_name
		return

	#q = Processes.find_one({'name':name})
	params = ['%s=%s' % (k,v) for k,v in kwargs.items()]
	cmdline =  plugin['executable'].split() + [transf_name] + params
	print "(%s) %s" % (plugin['working_dir'],cmdline)
	p = subprocess.Popen(cmdline, cwd=plugin['working_dir'])
	out = p.communicate()

def print_usage():
	print "usage: python admin.py <command>"
	print "where command is:"
	print "\timport_plugins"
	print "\tlist_plugins"
	print "exec <plugin> <transf> [[param=value] [param=value] ...]"
	print ""

import sys
def main():
	if len(sys.argv) < 2: 
		print_usage()
		return

	cmd = sys.argv[1]
	if cmd == 'import_plugins':
		import_plugins()
	if cmd == 'list_plugins':
		list_plugins()
	if cmd == 'exec':
		execute_plugin(sys.argv[2], sys.argv[3], **dict(x.split('=') for x in sys.argv[4:]))

if __name__ == '__main__':
	main()