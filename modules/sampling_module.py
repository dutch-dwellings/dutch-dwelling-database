import os
import random
import sys
import collections

from psycopg2.extras import NumericRange

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule
from utils.probability_utils import ProbabilityDistribution

class SamplingModule(BaseModule):

	def __init__(self, connection, regional_modules):
		super().__init__(connection)
		self.code_dict = {
		'district_heating_space' : 'sh01',
		'gas_boiler_space' : 'sh02',
		'block_heating_space' : 'sh03',
		'electric_heat_pump_space' : 'sh04',
		'electric_boiler_space' : 'sh05',
		'hybrid_heat_pump_space' : 'sh06',
		'district_heating_water' : 'wh01',
		'gas_boiler_water' : 'wh02',
		'block_heating_water' : 'wh03',
		'electric_heat_pump_water' : 'wh04',
		'elec_boiler_water' : 'wh05',
		'gas_cooking' : 'co01',
		'electric_cooking' : 'co02'
		}
		self.functions = ('space', 'water', 'cooking')

	def process(self, dwelling):
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return

		# First sampling
		for name, options in dwelling.outputs.items():
			if options.get('sampling', False) == True:
				distribution_value = dwelling.attributes[options['distribution']]
				dwelling.attributes[name] = self.sample(distribution_value, options['type'], name)
				self.check_water_space_dependency(dwelling, name)

		# Minimum of one installation each for space heating, water heating and cooking
		self.check_minimum_installations(dwelling)
		# Produce more convenient output
		self.produce_output_code(dwelling)

	outputs = {
		'space_heating': {
			'type': 'varchar'
		},
		'water_heating': {
			'type': 'varchar'
		},
		'cooking': {
			'type': 'varchar'
		}
	}

	def sample(self, value, output_type, name):
		if output_type == 'boolean':
			return self.sample_boolean(value, name)
		elif output_type == 'double precision':
			return self.sample_double_precision(value, name)
		elif output_type == 'numrange':
			return self.sample_numrange(value, name)
		else:
			raise NotImplementedError(f'SamplingModule has no sample method for output_type {output_type} yet')

	def sample_boolean(self, value, name):
		if type(value) not in [float, int]:
			raise ValueError(f"Expected type 'float' while sampling for boolean, but got: {type(value)}, for distribution: {name}")
		if (value < 0) or (value > 1):
			raise ValueError(f"Expected value between 0-1 while sampling for boolean, but got: {value}, for distribution: {name}")

		cutoff = random.random()
		if value < cutoff:
			return False
		else:
			return True

	def sample_double_precision(self, value, name):
		'''
		Gets the mean from a ProbabilityDistribution.
		'''
		if type(value) is not ProbabilityDistribution:
			raise NotImplementedError(f'sample_double_precision() has not been implemented for type {type(value)}')
		return value.mean

	def sample_numrange(self, value, name):
		'''
		Gets the 95% interval from a ProbabilityDistribution.
		'''
		if type(value) is not ProbabilityDistribution:
			raise NotImplementedError(f'sample_numrange() has not been implemented for type {type(value)}')
		interval = value.interval(0.95)
		# This is the Psycopg2 way to return a numrange.
		# We round to 2 decimals for presentation.
		return NumericRange(round(interval[0], 2), round(interval[1], 2), bounds='[]')

	def count_installations(self, dwelling, function):
		installations_amount = 0
		for name, options in dwelling.outputs.items():
			if options.get('sampling', False) == True and options.get('function', False) == function and dwelling.attributes[name] == True:
				installations_amount += 1
		return installations_amount

	def check_minimum_installations(self, dwelling):
		for function in self.functions:
			# Check whether an installation has been assigned
			installations_amount = self.count_installations(dwelling, function)
			tries = 0
			# Sample until installation is assigned or assign gas after five failed attempts as it is the most common
			while installations_amount == 0:
				self.get_sampling_outputs_per_function(dwelling, function)
				tries += 1
				if tries >= 4:
					if function == 'space':
						dwelling.attributes['gas_boiler_space'] = True
					if function == 'water':
						dwelling.attributes['gas_boiler_water'] = True
					if function == 'cooking':
						dwelling.attributes['gas_cooking'] = True
				installations_amount = self.count_installations(dwelling, function)

	def get_sampling_outputs_per_function(self, dwelling, function):
		for name, options in dwelling.outputs.items():
			if options.get('sampling', False) == True and options.get('function', False) == function:
					distribution_value = dwelling.attributes[options['distribution']]
					dwelling.attributes[name] = self.sample(distribution_value, options['type'], name)
					self.check_water_space_dependency(dwelling, name)

	def check_water_space_dependency(self, dwelling, name):
		if name == 'district_heating_water' and dwelling.attributes['district_heating_space'] == False:
			dwelling.attributes['district_heating_water'] = False
		elif name == 'electric_heat_pump_water' and dwelling.attributes['electric_heat_pump_space'] == False:
			dwelling.attributes['electric_heat_pump_water'] = False
		elif name == 'block_heating_water' and dwelling.attributes['block_heating_space'] == False:
			dwelling.attributes['block_heating_water'] = False

	def produce_output_code(self, dwelling):
		codes = collections.defaultdict(list)

		for function in self.functions:
			for name, options in dwelling.outputs.items():
				if options.get('sampling', False) == True and options.get('function', False) == function and dwelling.attributes[name] == True:
					codes[function].append(self.code_dict[name])

		space_code =  '_'.join(codes['space'])
		water_code =  '_'.join(codes['water'])
		cooking_code =  '_'.join(codes['cooking'])

		dwelling.attributes['space_heating'] = space_code
		dwelling.attributes['water_heating'] = water_code
		dwelling.attributes['cooking'] = cooking_code
