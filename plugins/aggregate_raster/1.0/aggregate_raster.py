import requests
import dateutil.parser
import datetime as dt
import simplejson
import subprocess
import os
import uuid
import shutil
import radstore_client

radstore_client.config.base_url = os.environ.get('RADSTORE_API_URL','http://127.0.0.1:3003/api/v1')

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

    prods = radstore_client.Product.query().filter(**url_params)
    params = {}

    tmpdir = '/tmp/aggregate_raster/%s' % uuid.uuid1()
    try: os.makedirs(tmpdir)
    except: pass

    AlphaList=["A","B","C","D","E","F","G","H","I","J","K","L","M",
        "N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]

    cmdline = ['/usr/bin/python','/usr/bin/gdal_calc.py']
    params = {}

    transf = radstore_client.Transformation()
    transf.datetime = dt.datetime.now()
    transf.process = aggregate_raster

    for i,prod in enumerate(prods):
        fname = '%s.tiff' % AlphaList[i]
        with open(os.path.join(tmpdir,fname), 'w') as fo:
            fo.write(prod.content)
        params[AlphaList[i]] = fname
        transf.add_input(prod)
    
    for k,v in params.items(): cmdline.extend(['-%s' % k, v])

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

        outp = radstore.Product()
        outp.type = 'geotiff.aggregated'
        outp.datetime = datetime
        outp.operation = op
        outp.name = '%s_%s_%s.tiff' % (datetime,duration,op)
        for k,v in filters.items():
            setattr(outp,k,v)
        outp.duration = duration

        outp.save()
        with open(os.path.join(tmpdir,'%s.tiff' % op)) as f:
            outp.content = f.read()
        outp.save_content()
        transf.add_output(outp)

    transf.save()
    shutil.rmtree(tmpdir)


import sys
def main():
    cmd,args = radstore_client.parse_cmdline(sys.argv)
    if cmd == 'aggregate':
        aggregate(**args)

if __name__ == '__main__':
    main()
