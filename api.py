import cherrypy
import pymongo
import simplejson
from bson.objectid import ObjectId
import dateutil.parser
#from cherrypy.lib.static import serve_file
from static import serve_gzip_file
import os
import random
import gzip

client = pymongo.MongoClient()
db = client['radar']

class MongoModel(object):	
	DEFAULT_LIMIT = 20

	def __init__(self, collname):
		self.coll = db[collname]

	def process_pagination_params(self, q, **kwargs):
		if 'offset' in kwargs: q = q.skip(int(kwargs['offset']))
		q = q.limit(int(kwargs.get('limit',self.DEFAULT_LIMIT)))
		return q

	def process_filter_params(self, q, **kwargs):
		flt = {}
		for k,v in kwargs.items():
			if k == 'limit' or k == 'offset': continue
			v = self.parse_value(v)
			if '.' in k: 
				k,op = k.split('.')[:2]
				if op == 'in': flt[k] = {'$in': [self.parse_value(x) for x in v.split(',')]}
				else: flt[k] = {'$' + op: v}
			else:
				flt[k] = v
		q = q.find(flt)
		return q

	def parse_value(self, v):
		try: return dateutil.parser.parse(v)
		except: pass

		try: return ObjectId(v)
		except: pass

		try: 
			if '.' in v: return float(v)
		except: pass

		try: return int(v)
		except: pass

		return v

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
		return simplejson.dumps(ans, default=str)


class Products(MongoModel):
	exposed = True
	fs_dir = os.path.join(os.path.split(os.path.abspath(__file__))[0],'fs')

	def __init__(self):
		super(Products, self).__init__('product')

	def GET(self, id=None, content=None, **kwargs):
		if id is None:
			q = self.process_filter_params(self.coll, **kwargs)
			count = q.count()
			limit = int(kwargs.get('limit',self.DEFAULT_LIMIT))
			if limit == 0:
				q = []
			else:
				q = self.process_pagination_params(q, **kwargs)
			
			return self.build_response('ok', **{
					'count': count,
					'limit': limit,
					'offset': int(kwargs.get('offset',0)),
					'products': list(q)
				})
		else:
			if content == 'content':
	 			return serve_gzip_file(os.path.join(self.fs_dir,id), "application/x-download", "attachment")
	 		else:
				q = self.coll.find_one({'_id':ObjectId(id)})
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

	#@cherrypy.tools.json_in()
	def POST(self, id=None, content=None, metadata=None, **kwargs):
		if id is None:
			if metadata is None: 
				metadata = simplejson.load(cherrypy.request.body)
			metadata['content_length'] = 0
			id = self.coll.insert_one(metadata).inserted_id
			return self.build_response('ok',**dict(product={'_id':id}))

		else:
			if content == 'content':
				size = self.upload_file(id)
				self.coll.update_one({'_id': ObjectId(id)},{'$set':{'content_length':size}})
				return self.build_response('ok',**dict(product={'_id':id}))

			else:
				return self.build_response('error',message='cannot POST metadata for an existing product. Use PUT instead.')

	def PUT(self, id, **kwargs):
		metadata = simplejson.load(cherrypy.request.body)
		coll.update_one({'_id':ObjectId(id)}, metadata)
		return self.build_response('ok',**dict(product={'_id':id}))



class Transformations(MongoModel):
	exposed = True

	def __init__(self):
		super(Transformations, self).__init__('transformation')

	def GET(self, id=None, **kwargs):
		if id is None:
			q = self.process_filter_params(self.coll, **kwargs)
			q = self.process_pagination_params(q, **kwargs)
			
			return self.build_response('ok', **{
					'count': q.count(),
					'limit': kwargs.get('limit',self.DEFAULT_LIMIT),
					'offset': kwargs.get('offset',0),
					'transformations': list(q)
				})
		else:
			q = self.coll.find_one({'_id':ObjectId(id)})
			return self.build_response('ok', **dict(transformation=q))

	def POST(self, id=None, outputs=None, **kwargs):
		if id is None:
			metadata = simplejson.load(cherrypy.request.body)
			id = self.coll.insert_one(metadata).inserted_id
			return self.build_response('ok', **dict(transformation={'_id':id}))

		else:
			if outputs == 'outputs':
				metadata = simplejson.load(cherrypy.request.body)
				resp = simplejson.loads(Products().POST(id=None, metadata=metadata))
				if resp['status'] != 'ok':
					return self.build_response('error', 
						message='error creating output product: %s' % resp['message'])
				self.coll.update_one({'_id':ObjectId(id)},{'$push':{'outputs':{'_id':ObjectId(resp['data']['product']['_id'])}}})
				return self.build_response('ok', **dict(product=resp['data']['product']))

			else:
				return self.build_response('error',message='cannot POST metadata for an existing transformation. Use PUT instead.')


# class FileSystem(object):
# 	exposed = True
# 	fs_dir = os.path.join(os.path.split(os.path.abspath(__file__))[0],'fs')

# 	def GET(self, id, **kwargs):
# 		print self.fs_dir
# 		return serve_file(os.path.join(self.fs_dir,id), "application/x-download", "attachment")

# 	def POST(self, **kwargs):
# 		id = ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyz') for i in range(24))
# 		with open(os.path.join(self.fs_dir,id),'w') as fo: 
# 			while True:
# 				data = cherrypy.request.body.read(8192)
# 				if not data: break
# 				fo.write(data)
		
# 		resp = {
# 			'sattus': 'ok',
# 			'data': {
# 				'file': id
# 			}
# 		}
# 		return simplejson.dumps(resp, default=str)


if __name__ == '__main__':

    cherrypy.tree.mount(
        Products(), '/api/v1/products',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        })
    cherrypy.tree.mount(    
        Transformations(), '/api/v1/transformations',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        }        
    )
    cherrypy.engine.start()
    cherrypy.engine.block()


