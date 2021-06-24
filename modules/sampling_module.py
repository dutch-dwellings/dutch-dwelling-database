import os
import random
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule

class SamplingModule(BaseModule):

	functions = ('space', 'water', 'cooking')

	def process(self, dwelling):
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return

		for name, options in dwelling.outputs.items():
			if options.get('sampling', False) == True:
				distribution_value = dwelling.attributes[options['distribution']]
				dwelling.attributes[name] = self.sample(distribution_value, options['type'], name)

		self.check_space_heating(dwelling)
		self.check_water_heating(dwelling)
		self.check_cooking(dwelling)

	def check_space_heating(self, dwelling):
		space_heating_installations_amount =  dwelling.attributes['district_heating_space'] + dwelling.attributes['hybrid_heat_pump'] + dwelling.attributes['electric_heat_pump'] + dwelling.attributes['electric_boiler'] + dwelling.attributes['gas_boiler_space'] + dwelling.attributes['block_heating_space']
		while space_heating_installations_amount == 0:
			self.get_sampling_outputs_per_function('space', dwelling)
			space_heating_installations_amount =  dwelling.attributes['district_heating_space'] + dwelling.attributes['hybrid_heat_pump'] + dwelling.attributes['electric_heat_pump'] + dwelling.attributes['electric_boiler'] + dwelling.attributes['gas_boiler_space'] + dwelling.attributes['block_heating_space']

	def check_water_heating(self, dwelling):
		water_heating_installations_amount = dwelling.attributes['district_heating_water'] + dwelling.attributes['elec_boiler_water'] + dwelling.attributes['electric_heat_pump_water'] + dwelling.attributes['gas_boiler_water'] + dwelling.attributes['block_heating_water']
		while water_heating_installations_amount == 0:
			self.get_sampling_outputs_per_function('water', dwelling)
			water_heating_installations_amount = dwelling.attributes['district_heating_water'] + dwelling.attributes['elec_boiler_water'] + dwelling.attributes['electric_heat_pump_water'] + dwelling.attributes['gas_boiler_water'] + dwelling.attributes['block_heating_water']

	def check_cooking(self, dwelling):
		cooking_installations_amount = dwelling.attributes['gas_cooking'] + dwelling.attributes['electric_cooking']
		while cooking_installations_amount == 0:
			self.get_sampling_outputs_per_function('cooking', dwelling)
			cooking_installations_amount = dwelling.attributes['gas_cooking'] + dwelling.attributes['electric_cooking']

	def get_sampling_outputs_per_function(self, function, dwelling):
		for name, options in dwelling.outputs.items():
			if options.get('sampling', False) == True:
				if options.get('function', False) == function:
					distribution_value = dwelling.attributes[options['distribution']]
					dwelling.attributes[name] = self.sample(distribution_value, options['type'], name)

	def sample(self, value, output_type, name):
		if output_type == 'boolean':
			return self.sample_boolean(value, name)
		else:
			raise NotImplementedError(f'SamplingModule has no sample method for output_type {output_type} yet')

	def sample_boolean(self, value, name):
		if type(value) != float:
			raise ValueError(f"Expected type 'float' while sampling for boolean, but got: {type(value)}, for distribution: {name}")
		if (value < 0) or (value > 1):
			raise ValueError(f"Expected value between 0-1 while sampling for boolean, but got: {value}, for distribution: {name}")

		cutoff = random.random()
		if value < cutoff:
			return False
		else:
			return True
