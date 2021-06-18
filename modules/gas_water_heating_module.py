import os
import sys

sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule


class GasWaterHeatingModule(BaseModule):

	def process(self, dwelling):
		super().process(dwelling)

		# Get dwelling attributes
		vbo_id = dwelling.attributes['vbo_id']
		gas_use_percentile_neighbourhood = dwelling.attributes['gas_use_percentile_neighbourhood']

		boiler_heating_space_p = dwelling.attributes['boiler_heating_space_p']
		district_low_gas_p = dwelling.attributes['district_low_gas_p']
		district_high_gas_p = dwelling.attributes['district_high_gas_p']
		elec_high_gas = dwelling.attributes['elec_high_gas_p']
		elec_low_gas_p = dwelling.attributes['elec_low_gas_p']
		block_heating_space_p = dwelling.attributes['block_heating_space_p']

		# Individual gas boiler
		gas_boiler_water_p = boiler_heating_space_p + district_low_gas_p + district_high_gas_p + elec_high_gas + elec_low_gas_p
		gas_boiler_water_p = self.modify_probability_up(gas_boiler_water_p, gas_use_percentile_neighbourhood)

		# Block gas boiler
		block_heating_water_p = block_heating_space_p

		dwelling.attributes['gas_boiler_water_p'] = gas_boiler_water_p
		dwelling.attributes['block_heating_water_p'] = block_heating_water_p

	outputs = {
		'gas_boiler_water': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'gas_boiler_water_p'
		},
		'gas_boiler_water_p': {
			'type': 'float',
			'sampling': False,
		},
		'block_heating_water': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'block_heating_water_p'
		},
		'block_heating_water_p': {
			'type': 'float',
			'sampling': False,
		}
	}
