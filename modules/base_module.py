import os
import sys

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database_utils import add_column

class BaseModule:

	def __init__(self, connection, **kwargs):
		if 'silent' not in kwargs or not kwargs['silent']:
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

	def modify_probability_up(self, probability, percentile):
		# A high value for percentile will increase the probability
		if probability > 0.5:
			probability = probability + 2 * (1 - probability) * (percentile - 0.5)
		else:
			probability = probability + 2 * (probability) * (percentile - 0.5)
		return probability

	def modify_probability_down(self, probability, percentile):
		# A high value for percentile will decrease the probability
		if probability > 0.5:
			probability = probability - 2 * (1 - probability) * (percentile - 0.5)
		else:
			probability = probability - 2 * (probability) * (percentile - 0.5)
		return probability

	def process(self, dwelling):
		# Check whether this module has already processed
		# this dwelling.
		if self.__class__.__name__ not in dwelling.processed_by:
			dwelling.outputs.update(self.outputs)
			dwelling.processed_by.append(self.__class__.__name__)
			return True
		# Module has already been seen, we need to signal
		# to child modules that we shouldn't continue processing.
		else:
			return False

	# Outputs need to be a dict, where:
	# - the keys are valid PostgreSQL identifiers
	# - the values are dicts:
	#	- type (mandatory): valid PostgreSQL data type
	#	- sampling: boolean (optional)
	#	- distribution: attribute name of distribution to sample from
	#		(mandatory when sampling=True)
	outputs = {}

class BaseRegionalModule:

	def __init__(self, connection):
		print(f'   Initiating regional module {self.__class__.__name__}')
		self.connection = connection

	# Indicates support for different regional types.
	# Current options: ['pc6'], ['buurt'].
	# If you want to add a new region type, then also
	# add that type to the definition of
	# RegionsModule.regional_modules
	supports = []
