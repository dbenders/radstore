import cherrypy
import simplejson
from bson.objectid import ObjectId
import dateutil.parser
#from cherrypy.lib.static import serve_file
from static import serve_gzip_file
import os
import random
import gzip
import subprocess
import datetime
import pymongo

from models import Products, Processes, Transformations, ProductTypes

class MongoController(object):
	DEFAULT_LIMIT = 20

	def __init__(self, dao, name_singular, name_plural):
		self.name_singular = name_singular
		self.name_plural = name_plural
		self.dao = dao

	def process_pagination_params(self, q, **kwargs):
		if 'offset' in kwargs: q = q.skip(int(kwargs['offset']))
		q = q.limit(int(kwargs.get('limit',self.DEFAULT_LIMIT)))
		return q

	def process_filter_params(self, q, **kwargs):
		fields = None
		if 'fields' in kwargs:
			fields = kwargs.pop('fields').split(',')
		flt = {}
		for k,v in kwargs.items():
			if k == 'limit' or k == 'offset': continue
			v = self.parse_value(v)
			if '.' in k and k.split('.')[-1].startswith('$'):
				x = k.split('.')
				k,op = '.'.join(x[:-1]),x[-1]
				if k not in flt: flt[k] = {}
				flt[k][op] = v
			else:
				flt[k] = v
		print flt
		q = q.find(flt, fields)
		return q

	def parse_json_value(self, v):
		try: return datetime.datetime.strptime(v,'%Y-%m-%dT%H:%M:%S')
		except: pass

		try: return datetime.datetime.strptime(v,'%Y-%m-%d %H:%M:%S')
		except: pass

		return v

	def parse_json_dict(self, d):
		return dict((k,self.parse_json_value(v)) for k,v in d.items())

	def parse_value(self, v):

		if ',' in v: return [self.parse_value(x) for x in v.split(',')]

		try: return ObjectId(v)
		except: pass

		try:
			if '.' in v: return float(v)
		except: pass

		try: return int(v)
		except: pass

		try: return dateutil.parser.parse(v)
		except: pass

		return v

	def OPTIONS(self, *args, **kwargs):
		cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
		if 'Access-Control-Request-Headers' in cherrypy.request.headers:
			cherrypy.response.headers['Access-Control-Allow-Headers'] = cherrypy.request.headers['Access-Control-Request-Headers']
		return "GET, POST"

	def build_response(self, status, message=None, **kwargs):
		if status == 'ok':
			ans = {
				'status': status,
				'data': kwargs
			}
			if message is not None: ans['message'] = message
		else:
			ans = {
				'status': status,
				'message': message
			}
		cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
		cherrypy.response.headers['Content-Type'] = 'application/json'
		return simplejson.dumps(ans, default=str)

	def GET(self, id=None, **kwargs):

		if id is None:
			q = self.process_filter_params(self.dao.collection, **kwargs)
			q = self.process_pagination_params(q, **kwargs)

			return self.build_response('ok', **{
					'count': q.count(),
					'limit': kwargs.get('limit',self.DEFAULT_LIMIT),
					'offset': kwargs.get('offset',0),
					self.name_plural: list(q)
				})
		else:
			q = self.dao.find_one({'_id':ObjectId(id)})
			return self.build_response('ok', **{self.name_singular: q})

class ProductTypesController(MongoController):
	exposed = True

	def __init__(self):
		super(ProductTypesController, self).__init__(ProductTypes,'product_type','product_types')

	def GET(self, name=None, **kwargs):
		if name is not None:
			if 'distinct' in kwargs:
				if kwargs['distinct'] == 'type':
					qq = {}
				else:
					qq = {'type':name}
				q = Products.distinct(kwargs['distinct'], qq)
				return self.build_response('ok', **{'attribute': kwargs['distinct'], 'values': q})
			else:
				q = ProductTypes.find_one({'name':name})
				return self.build_response('ok', **{self.name_singular: q})
		else:
			return super(ProductTypesController, self).GET(name, **kwargs)


class SummaryController(object):
	exposed = True


class ProductsController(MongoController):
	exposed = True
	fs_dir = os.path.join(os.path.split(os.path.abspath(__file__))[0],'fs')

	def __init__(self):
		super(ProductsController, self).__init__(Products,'product','products')

	def GET(self, id=None, content=None, **kwargs):
		if id is None:
			# if 'include' in kwargs:
			# 	include = kwargs.pop('include').split(',')
			# else:
			# 	include = []

			q = self.process_filter_params(Products.collection, **kwargs)

			count = q.count()
			limit = int(kwargs.get('limit',self.DEFAULT_LIMIT))
			if limit == 0:
				q = []
			else:
				q = self.process_pagination_params(q, **kwargs)
			q = q.sort([('datetime',pymongo.ASCENDING)])
			q = list(q)

			# if 'transformations' in include:
			# 	for doc in q:
			# 		qt = Transformations.find({'inputs._id':doc['_id']})
			# 		if qt.count() > 0:
			# 			doc['transformations'] = list(qt)

			return self.build_response('ok', **{
					'count': count,
					'limit': limit,
					'offset': int(kwargs.get('offset',0)),
					'products': q
				})
		else:
			if content == 'content':
				q = Products.find_one({'_id':ObjectId(id)})
	 			return serve_gzip_file(os.path.join(self.fs_dir,id), q['name'], "application/x-download", "attachment")
	 		else:
				if 'include' in kwargs:
					include = kwargs.pop('include').split(',')
				else:
					include = []

				q = Products.find_one({'_id':ObjectId(id)})

				# if 'transformations' in include:
				# 	qt = Transformations.find({'inputs._id':q['_id']})
				# 	if qt.count() > 0:
				# 		q['transformations'] = list(qt)

				return self.build_response('ok', **dict(product=q))

	def upload_file(self, id):
		size = 0
		with gzip.open(os.path.join(self.fs_dir,id),'w') as fo:
			while True:
				data = cherrypy.request.body.read(8192)
				if not data: break
				size += len(data)
				fo.write(data)
		return size

	def POST(self, id=None, content=None, metadata=None, **kwargs):
		if id is None:
			if metadata is None:
				metadata = self.parse_json_dict(simplejson.load(cherrypy.request.body))
			metadata['content_length'] = 0
			id = Products.insert_one(metadata).inserted_id
			return self.build_response('ok',**dict(product={'_id':id}))

		else:
			if content == 'content':
				size = self.upload_file(id)
				Products.update_one({'_id': ObjectId(id)},{'$set':{'content_length':size}})
				return self.build_response('ok',**dict(product={'_id':id}))

			else:
				return self.build_response('error',message='cannot POST metadata for an existing product. Use PUT instead.')

	def PUT(self, id, **kwargs):
		metadata = self.parse_json_dict(simplejson.load(cherrypy.request.body))
		Products.update_one({'_id':ObjectId(id)}, {'$set':metadata})
		return self.build_response('ok',**dict(product={'_id':id}))


class ProcessesController(MongoController):
	exposed = True

	def __init__(self):
		super(ProcessesController, self).__init__(Processes,'process','processes')

	def GET(self, name=None, transformation=None, **kwargs):
		if name is not None:
			q = Processes.find_one({'name':name})
			cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
			return self.build_response('ok', **{'process':q})
		else:
			return super(ProcessesController, self).GET(name, **kwargs)

	def POST(self, name, transformation, **kwargs):
		params = ['%s=%s' % (k,v) for k,v in simplejson.load(cherrypy.request.body).items()]
		q = Processes.find_one({'name':name})
		cmdline =  q['executable'].split() + [transformation] + params
		print "(%s) %s" % (q['working_dir'],cmdline)
		p = subprocess.Popen(cmdline, cwd=q['working_dir'])
		out = p.communicate()
		cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
		return self.build_response('ok')

class TransformationsController(MongoController):
	exposed = True

	def __init__(self):
		super(TransformationsController, self).__init__(Transformations,'transformation','transformations')

	def GET(self, id=None, **kwargs):
		if id is None:
			q = self.process_filter_params(Transformations.collection, **kwargs)
			q = self.process_pagination_params(q, **kwargs)

			return self.build_response('ok', **{
					'count': q.count(),
					'limit': kwargs.get('limit',self.DEFAULT_LIMIT),
					'offset': kwargs.get('offset',0),
					'transformations': list(q)
				})
		else:
			q = Transformations.find_one({'_id':ObjectId(id)})
			return self.build_response('ok', **dict(transformation=q))

	def POST(self, id=None, outputs=None, **kwargs):
		if id is None:
			metadata = self.parse_json_dict(simplejson.load(cherrypy.request.body))
			for inp in metadata.get("inputs",[]):
				if '_id' in inp: inp['_id'] = self.parse_value(inp['_id'])

			id = Transformations.insert_one(metadata).inserted_id

			# for inp in metadata.get("inputs",[]):
			# 	Products.update_one({'_id':inp['_id']},{'$push':{'transformations':{'_id':id}}})

			return self.build_response('ok', **dict(transformation={'_id':id}))

		else:
			if outputs == 'outputs':
				metadata = self.parse_json_dict(simplejson.load(cherrypy.request.body))
				resp = simplejson.loads(ProductsController().POST(id=None, metadata=metadata))
				if resp['status'] != 'ok':
					return self.build_response('error',
						message='error creating output product: %s' % resp['message'])
				Transformations.update_one({'_id':ObjectId(id)},{'$push':{'outputs':{'_id':ObjectId(resp['data']['product']['_id'])}}})
				return self.build_response('ok', **dict(product=resp['data']['product']))

			else:
				return self.build_response('error',message='cannot POST metadata for an existing transformation. Use PUT instead.')


if __name__ == '__main__':

    cherrypy.tree.mount(
        ProductsController(), '/api/v1/products',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        })
    cherrypy.tree.mount(
        ProductTypesController(), '/api/v1/product_types',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        })
    cherrypy.tree.mount(
        TransformationsController(), '/api/v1/transformations',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        })
    cherrypy.tree.mount(
        SummaryController(), '/api/v1/summary',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        })
    cherrypy.tree.mount(
        ProcessesController(), '/api/v1/procs',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        }
    )
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': 3003,
                       })
    cherrypy.engine.start()
    cherrypy.engine.block()
