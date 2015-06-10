import pymongo

client = pymongo.MongoClient()
db = client['radar']

class MongoDAO(object):
	def __init__(self, collname):
		self.coll = db[collname]

	@property
	def collection(self):
		return self.coll

	def find(self, *args, **kwargs):
		print "%s, %s" % (args,kwargs)
		return self.coll.find(*args, **kwargs)

	def find_one(self, *args, **kwargs):
		return self.coll.find_one(*args, **kwargs)

	def insert_one(self, *args, **kwargs):
		return self.coll.insert_one(*args, **kwargs)

	def update_one(self, *args, **kwargs):
		return self.coll.update_one(*args, **kwargs)

	def distinct(self, *args, **kwargs):
		return self.coll.distinct(*args, **kwargs)


Products = MongoDAO('product')
ProductTypes = MongoDAO('product_type')
Transformations = MongoDAO('transformation')
Processes = MongoDAO('plugin')
