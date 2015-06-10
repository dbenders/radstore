import requests
import dateutil.parser
import datetime as dt
import simplejson
import subprocess
import os

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
    resp = check_result(requests.get('http://localhost:8080/api/v1/products',url_params))
    params = {}

    tmpdir = '/tmp/aggregate_raster/'
    try: os.makedirs(tmpdir)
    except: pass

    AlphaList=["A","B","C","D","E","F","G","H","I","J","K","L","M",
        "N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]

    cmdline = ['/usr/bin/python','/usr/bin/gdal_calc.py','--outfile','out.tiff','--overwrite']
    params = {}

    transformation_metadata = {
        'datetime': dt.datetime.now(),
        'process': 'aggregate_raster',
        'inputs': []
    }

    for i,prod in enumerate(resp['data']['products']):
        resp = requests.get('http://localhost:8080/api/v1/products/%s/content' % prod['_id'])
        fname = '%s.tiff' % AlphaList[i]
        with open(os.path.join(tmpdir,fname), 'w') as fo:
            fo.write(resp.content)
        params[AlphaList[i]] = fname
        transformation_metadata['inputs'].append({'_id':prod['_id']})
    
    for k,v in params.items(): cmdline.extend(['-%s' % k, v])


    resp_data = check_result(
        requests.post('http://localhost:8080/api/v1/transformations', 
            data=simplejson.dumps(transformation_metadata, default=str)))
    transformation_id = resp_data['data']['transformation']['_id']


    if operation == 'all':
        ops = ['avg','max','min']
    else:
        ops = [operation]

    for op in ops:
        if op == 'avg':
            cmdline.extend(['--calc','(%s)/%d' % ('+'.join(params.keys()),len(params))])
        elif op == 'max':
            cmdline.extend(['--calc','maximum(%s)' % ','.join(params.keys())])      
        elif op == 'min':
            cmdline.extend(['--calc','minimum(%s)' % ','.join(params.keys())])      

        print cmdline
        p = subprocess.Popen(cmdline, cwd=tmpdir)
        out = p.communicate()

        output_metadata = {
            'type': 'geotiff.aggregated',
            'datetime': datetime,
            'duration': duration,
            'operation': op,
            'name': '%s_%s_%s.tiff' % (datetime,duration,operation)
        }
        output_metadata.update(filters)

        resp_data = check_result(
            requests.post('http://localhost:8080/api/v1/transformations/%s/outputs' % transformation_id,
                data=simplejson.dumps(output_metadata,default=str)))

        output_id = resp_data['data']['product']['_id']

        with open(os.path.join(tmpdir,'out.tiff')) as f:
            data = f.read()
        resp_data = check_result(
            requests.post('http://localhost:8080/api/v1/products/%s/content' % output_id, 
                data=data))


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