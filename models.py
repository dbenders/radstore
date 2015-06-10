import pymongo

db = pymongo.MongoClient()['radar']

class MongoModel(object):
	def __init__(self, collname):
		self.collection = db[collname]

	def find(self, *args, **kwargs):
		return self.collection.find(*args, **kwargs)

	def find_one(self, *args, **kwargs):
		return self.collection.find_one(*args, **kwargs)

	def update(self, *args, **kwargs):
		return self.collection.update(*args, **kwargs)

	def update_one(self, *args, **kwargs):
		return self.collection.update_one(*args, **kwargs)

	def insert_one(self, *args, **kwargs):
		return self.collection.insert_one(*args, **kwargs)

Products = MongoModel('product')
Processes = MongoModel('process')
Transformations = MongoModel('transformation')
ProductTypes = MongoModel('product_type')
