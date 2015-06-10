import sys

def aggregate(operation, source, **kwargs):
	


def process_arg(arg):
	k,v = arg.split('=')
	if ',' in v: v = v.split(',')
	return k,v

def main():
	cmd = sys.argv[1]
	if cmd == 'aggregate':
		aggregate(**dict(map(process_arg, sys.argv[2:])))
