import requests
import dateutil.parser
import datetime as dt
import simplejson
import subprocess
import os
import uuid
import shutil

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

def op_tree(op, args):
    if len(args) == 1: return args[0]
    elif len(args) % 2 == 1:
        l,r = args[0],op_tree(op,args[1:])
    else:
        m = len(args)/2
        l,r = op_tree(op,args[:m]),op_tree(op,args[m:])
    return "%s(%s,%s)" % (op,l,r)

def aggregate(datetime, duration, operation, filters="{}", **kwargs):

    duration = int(duration)
    datefrom = dateutil.parser.parse(datetime)
    dateto = datefrom + dt.timedelta(minutes=duration)
    
    url_params = {'type':'geotiff.original',
        'datetime.$gte': datefrom.isoformat(),
        'datetime.$lte': dateto.isoformat()}

    filters = simplejson.loads(filters)
    url_params.update(filters)
    print url_params
    resp = check_result(requests.get(api_url+'/products',url_params))
    params = {}

    tmpdir = '/tmp/aggregate_raster/%s' % uuid.uuid1()
    try: os.makedirs(tmpdir)
    except: pass

    AlphaList=["A","B","C","D","E","F","G","H","I","J","K","L","M",
        "N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]

    cmdline = ['/usr/bin/python','/usr/bin/gdal_calc.py']
    params = {}

    transformation_metadata = {
        'datetime': dt.datetime.now(),
        'process': 'aggregate_raster',
        'inputs': []
    }

    for i,prod in enumerate(resp['data']['products']):
        resp = requests.get('%s/products/%s/content' % (api_url,prod['_id']))
        fname = '%s.tiff' % AlphaList[i]
        with open(os.path.join(tmpdir,fname), 'w') as fo:
            fo.write(resp.content)
        params[AlphaList[i]] = fname
        transformation_metadata['inputs'].append({'_id':prod['_id']})
    
    for k,v in params.items(): cmdline.extend(['-%s' % k, v])


    resp_data = check_result(
        requests.post('%s/transformations' % api_url, 
            data=simplejson.dumps(transformation_metadata, default=str)))
    transformation_id = resp_data['data']['transformation']['_id']


    if operation == 'all':
        ops = ['avg','max','min']
    else:
        ops = [operation]

    cmdline_ori = cmdline
    for op in ops:
        cmdline = [x for x in cmdline_ori]
        cmdline.extend(['--outfile','%s.tiff' % op])
        if op == 'avg':
            cmdline.extend(['--calc','(%s)/%d' % ('+'.join(params.keys()),len(params))])
        elif op == 'max':
            cmdline.extend(['--calc',op_tree('fmax',params.keys())])
        elif op == 'min':
            cmdline.extend(['--calc',op_tree('fmin',params.keys())])

        print ' '.join(cmdline)
        p = subprocess.Popen(cmdline, cwd=tmpdir)
        out = p.communicate()

        output_metadata = {
            'type': 'geotiff.aggregated',
            'datetime': datetime,
            'duration': duration,
            'operation': op,
            'name': '%s_%s_%s.tiff' % (datetime,duration,op)
        }
        output_metadata.update(filters)
        output_metadata['duration'] = duration

        resp_data = check_result(
            requests.post('%s/transformations/%s/outputs' % (api_url,transformation_id),
                data=simplejson.dumps(output_metadata,default=str)))

        output_id = resp_data['data']['product']['_id']

        with open(os.path.join(tmpdir,'%s.tiff' % op)) as f:
            data = f.read()
        resp_data = check_result(
            requests.post('%s/products/%s/content' % (api_url,output_id), 
                data=data))

    shutil.rmtree(tmpdir)


def process_arg(arg):
    p = arg.split('=')
    k,v = p[0], '='.join(p[1:])
    #if ',' in v: v = v.split(',')
    return k,v

import sys
def main():
    cmd = sys.argv[1]
    if cmd == 'aggregate':
        aggregate(**dict(map(process_arg, sys.argv[2:])))

if __name__ == '__main__':
    main()
