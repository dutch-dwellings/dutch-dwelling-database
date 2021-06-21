import pprint
from utils.database_utils import insert_dict

class Dwelling:

	def __init__(self, attributes, connection):
		self.attributes = attributes
		self.connection = connection
		# We copy the list so we get an instance variable
		# instead of a class variable.
		self.outputs = self.default_outputs.copy()
		self.sampling_outputs = {}
		self.regions = {}

	def __str__(self):
		pp = pprint.PrettyPrinter(indent=4)
		return f'Dwelling {self.attributes["vbo_id"]}:\nattributes:\n{pp.pformat(self.attributes)}\noutputs:\n{pp.pformat(self.outputs)}'

	def __repr__(self):
		return f'Dwelling(attributes={repr(self.attributes)}, connection={repr(self.connection)})'

	def get_output_attributes(self):
		'''
		Get the attributes and their values
		that need to be output to the database.
		'''
		return {key: val for (key, val) in self.attributes.items() if key in self.outputs.keys()}

	def save(self):
		'''
		INSERT the generated Dwelling object
		into the 'results' database.
		'''
		cursor = self.connection.cursor()

		row_dict = self.get_output_attributes()
		insert_dict(
			table_name='results',
			row_dict = row_dict,
			cursor = cursor
		)

		cursor.close()

	# This defines the default outputs irrespective of which
	# modules are active. Specify the outputs for specific modules
	# within the class definition of that module.
	#
	# This has to match the default 'results'
	# table layout as defined in utils/create_results_table.sql.
	# In other words: columns have to exist for all the
	# default_outputs.
	#
	# As of now, we can only assume that BAG-data is always present,
	# so only use BAG column_names here.
	default_outputs = {'vbo_id': {}}

class PlaceholderDwelling(Dwelling):

	def __init__(self, vbo_id):
		pass

class Region:

	def __init__(self):
		self.dwellings = []

class PC6(Region):

	def __init__(self, pc6, pc6_modules, connection):
		super().__init__()
		self.attributes = {'pc6': pc6}
		self.connection = connection
		self.dwellings = self.get_placeholder_dwellings()
		for module in pc6_modules:
			module.process_pc6(self)

	def get_placeholder_dwellings(self):
		query = "SELECT vbo_id FROM bag WHERE pc6 = %s"
		cursor = self.connection.cursor()
		cursor.execute(query, self.attributes['pc6'])
		placeholder_dwellings = [PlaceholderDwelling(vbo_id) for (vbo_id) in cursor.fetchall()]
		return placeholder_dwellings

class Buurt(Region):

	def __init__(self, buurt_id, buurt_modules, connection):
		super().__init__()
		self.attributes = {'buurt_id': buurt_id}
		self.connection = connection
		self.dwellings = self.get_placeholder_dwellings()
		for module in buurt_modules:
			module.process_buurt(self)

	def get_placeholder_dwellings(self):
		query = "SELECT vbo_id FROM bag WHERE buurt_id = %s"
		cursor = self.connection.cursor()
		cursor.execute(query, self.attributes['buurt_id'])
		placeholder_dwellings = [PlaceholderDwelling(vbo_id) for (vbo_id) in cursor.fetchall()]
		return placeholder_dwellings
