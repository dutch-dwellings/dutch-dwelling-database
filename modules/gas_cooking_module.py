import os
import sys

sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule


class GasCookingModule(BaseModule):

	def process(self, dwelling, **kwargs):
		super().process(dwelling)

		# Get dwelling attributes
		gas_use_percentile_neighbourhood = dwelling.attributes['gas_use_percentile_neighbourhood']

		district_high_gas_p = dwelling.attributes['district_high_gas_p']
		district_low_gas_p = dwelling.attributes['district_low_gas_p']
		elec_high_gas_p = dwelling.attributes['elec_high_gas_p']
		elec_low_gas_p = dwelling.attributes['elec_low_gas_p']
		boiler_heating_space_p = dwelling.attributes['boiler_heating_space_p']
		block_heating_space_p = dwelling.attributes['block_heating_space_p']

		# Add and modify probabilities
		gas_cooking_p = boiler_heating_space_p + district_high_gas_p + district_low_gas_p + elec_high_gas_p + elec_low_gas_p + block_heating_space_p
		gas_cooking_p = self.modify_probability_up(gas_cooking_p,gas_use_percentile_neighbourhood)

		dwelling.attributes['gas_cooking_p'] = gas_cooking_p

	outputs = {
		'gas_cooking': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'gas_cooking_p'
		},
		'gas_cooking_p': {
			'type': 'float',
			'sampling': False,
		}
	}
