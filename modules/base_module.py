from database_utils import add_column

class BaseModule:

	def __init__(self, connection):
		self.connection = connection
		self.create_required_columns()

	def create_required_columns(self):
		'''
		Make sure the required columns for the data outputs
		exist.
		'''
		for column_name, data_type in self.outputs.items():
			add_column(
				table_name='results',
				column_name=column_name,
				data_type=data_type,
				connection=self.connection
			)

	def process(self, dwelling):
		dwelling.outputs.extend(self.outputs.keys())

	# Outputs need to be a dict, where:
	# - the keys are valid PostgreSQL identifiers
	# - the values are valid PostgreSQL data types
	outputs = {}