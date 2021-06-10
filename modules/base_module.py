import os
import sys

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database_utils import add_column

class BaseModule:

	def __init__(self, connection):
		print(f'   Initiating module {self.__class__.__name__}')
		self.connection = connection
		self.create_required_columns()

	def create_required_columns(self):
		'''
		Make sure the required columns for the data outputs
		exist.
		'''
		for output_name, options in self.outputs.items():
			add_column(
				table_name='results',
				column_name=output_name,
				data_type=options['type'],
				connection=self.connection
			)

	def process(self, dwelling):
		dwelling.outputs.update(self.outputs)

	# Outputs need to be a dict, where:
	# - the keys are valid PostgreSQL identifiers
	# - the values are dicts:
	#	- type (mandatory): valid PostgreSQL data type
	#	- sampling: boolean (optional)
	#	- distribution: attribute name of distribution to sample from
	#		(mandatory when sampling=True)
	outputs = {}
