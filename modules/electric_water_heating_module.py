import os
import sys

sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule


class ElectricWaterHeatingModule(BaseModule):

	def __init__(self, connection, **kwargs):
		super().__init__(connection)

	def process(self, dwelling):
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return

		# Get dwelling attributes
		gas_use_percentile_neighbourhood = dwelling.attributes['gas_use_percentile_neighbourhood']
		elec_use_percentile_neighbourhood = dwelling.attributes['elec_use_percentile_neighbourhood']

		district_no_gas_p = dwelling.attributes['district_no_gas_p']
		elec_no_gas_p = dwelling.attributes['elec_no_gas_p']
		electric_heat_pump_p = dwelling.attributes['electric_heat_pump_p']

		# Electric boiler
		elec_boiler_water_p = district_no_gas_p + elec_no_gas_p
		elec_boiler_water_p = self.modify_probability_up(elec_boiler_water_p, elec_use_percentile_neighbourhood)

		# Heat pump
		electric_heat_pump_water_p = electric_heat_pump_p

		dwelling.attributes['elec_boiler_water_p'] = elec_boiler_water_p
		dwelling.attributes['electric_heat_pump_water_p'] = electric_heat_pump_water_p

	outputs = {
		'elec_boiler_water': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'elec_boiler_water_p'
		},
		'elec_boiler_water_p': {
			'type': 'float',
			'sampling': False,
		},
		'electric_heat_pump_water': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'electric_heat_pump_water_p'
		},
		'electric_heat_pump_water_p': {
			'type': 'float',
			'sampling': False,
		}
	}
