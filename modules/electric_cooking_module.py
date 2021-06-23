import os
import sys

sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule


class ElectricCookingModule(BaseModule):

	def process(self, dwelling, **kwargs):
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return

		# Get dwelling attributes
		elec_use_percentile_neighbourhood = dwelling.attributes['elec_use_percentile_neighbourhood']
		district_no_gas_p = dwelling.attributes['district_no_gas_p']
		elec_no_gas_p = dwelling.attributes['elec_no_gas_p']

		# Add and modify probabilities
		electric_cooking_p = district_no_gas_p + elec_no_gas_p
		electric_cooking_p = self.modify_probability_up(electric_cooking_p, elec_use_percentile_neighbourhood)

		dwelling.attributes['electric_cooking_p'] = electric_cooking_p

	outputs = {
		'electric_cooking': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'electric_cooking_p'
		},
		'electric_cooking_p': {
			'type': 'float',
			'sampling': False,
		}
	}
