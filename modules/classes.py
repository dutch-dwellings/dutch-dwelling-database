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
		self.processed_by = []

	def __str__(self):
		pp = pprint.PrettyPrinter(indent=4)
		return f'{self.__class__.__name__} {self.attributes["vbo_id"]}:\nattributes:\n{pp.pformat(self.attributes)}\noutputs:\n{pp.pformat(self.outputs)}'

	def __repr__(self):
		return f'{self.__class__.__name__}(attributes={repr(self.attributes)}, connection={repr(self.connection)})'

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

	pass

class Region:

	def __init__(self):
		self.dwellings = []

	def add_dwelling(self, dwelling):
		'''
		Replace the matching placeholder (on vbo_id) in self.dwellings
		by the actual dwelling. Also add information that we already
		gathered for the placeholder to the dwelling itself, to save
		processing time for the dwelling later on.
		'''
		vbo_id = dwelling.attributes['vbo_id']
		index = self.get_index_of_placeholder_dwelling(vbo_id)
		placeholder_dwelling = self.dwellings[index]
		self.dwellings[index] = dwelling

		# Adding info from placeholder to dwelling.
		for key in placeholder_dwelling.attributes:
			if key in dwelling.attributes:
				# We do an extra check to make sure we do not silently
				# overwrite existing information
				if placeholder_dwelling.attributes[key] != dwelling.attributes[key]:
					raise ValueError(f'Expected attributes of dwelling to equal those of the placeholder dwelling but they differ for key "{key}".\n\tDwelling: {dwelling.attributes[key]}\n\tPlaceholder dwelling: {placeholder_dwelling.attributes[key]}')
			else:
				dwelling.attributes[key] = placeholder_dwelling.attributes[key]

	def get_index_of_placeholder_dwelling(self, vbo_id):
		'''
		Gets the index in self.dwellings of the placeholder dwelling
		that matches the vbo_id. We check whether there is precisely 1
		that matches (there should be), and whether this is indeed
		of the type PlaceholderDwelling.
		'''
		indexes = [
			index
			for index, dwelling
			in enumerate(self.dwellings)
			if dwelling.attributes['vbo_id'] == vbo_id
		]

		if len(indexes) != 1:
			raise ValueError(f'Expected exactly 1 placeholder dwelling for vbo_id {vbo_id} but got {len(indexes)}.')

		index = indexes[0]
		dwelling = self.dwellings[index]

		if isinstance(dwelling, PlaceholderDwelling):
			return index
		else:
			raise ValueError(f'Expected dwelling at index {index} to be a placeholder dwelling, but it is of type {type(dwelling)}')

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
		cursor.execute(query, (self.attributes['pc6'],))
		placeholder_dwellings = [
			PlaceholderDwelling({'vbo_id': vbo_id}, self.connection)
			for (vbo_id, )
			in cursor.fetchall()
		]
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
		cursor.execute(query, (self.attributes['buurt_id'],))
		placeholder_dwellings = [
			PlaceholderDwelling({'vbo_id': vbo_id}, self.connection)
			for (vbo_id, )
			in cursor.fetchall()
		]
		return placeholder_dwellings
