import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule

class DistrictWaterHeatingModule(BaseModule):

	def __init__(self, connection):
		super().__init__(connection)

	def process(self, dwelling):
		super().process(dwelling)

		# Get dwelling attributes
		vbo_id = dwelling.attributes['vbo_id']
		gas_use_percentile_neighbourhood = dwelling.attributes['gas_use_percentile_neighbourhood']
		district_high_gas_p = dwelling.attributes['district_high_gas_p']
		district_low_gas_p = dwelling.attributes['district_low_gas_p']
		district_no_gas_p = dwelling.attributes['district_no_gas_p']

		# Water district heating
		district_heating_water_p = district_high_gas_p + district_low_gas_p + district_no_gas_p
		district_heating_water_p = self.modify_probability_down(district_heating_water_p, gas_use_percentile_neighbourhood)

		dwelling.attributes['district_heating_water_p'] = district_heating_water_p

	outputs = {
		'district_heating_water': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'district_heating_water_p'
			},
		'district_heating_water_p': {
			'type': 'float',
			'sampling': False,
			}
	}
