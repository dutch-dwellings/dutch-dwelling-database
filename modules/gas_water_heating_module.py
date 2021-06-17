import os
import sys
import re
import itertools
from scipy.interpolate import interp1d
import collections
from utils.database_utils import get_connection, get_neighbourhood_dwellings
from modules.dwelling import Dwelling

sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule


class GasWaterHeatingModule(BaseModule):

	def __init__(self, connection):
		super().__init__(connection)
		self.create_dicts()

	def create_dicts(self):
		self.buurten_gas_boiler_data = {}
		self.buurten_block_heating_data = {}
		self.neighbourhood_gas_check_dict = {}
		self.postcode_gas_use_data = {}
		self.gas_benchmark_dict = {}

	def process(self, dwelling):
		super().process(dwelling)

		# Individual gas boiler
		gas_boiler_water_p = dwelling.attributes['gas_boiler_space_p'] + dwelling.attributes['district_low_gas_p'] + dwelling.attributes['hybrid_heat_pump_p'] + dwelling.attributes['elec_low_gas_p']

		print('gas_boiler_space_p = ' + str(dwelling.attributes['gas_boiler_space_p'] ))
		print('district_low_gas_p = ' + str(dwelling.attributes['district_low_gas_p'] ))
		print('hybrid_heat_pump_p = '+ str(dwelling.attributes['hybrid_heat_pump_p'] ))
		print('elec_low_gas_p     = ' + str(dwelling.attributes['elec_low_gas_p'] ))
		print('elec_no_gas_p      = ' + str(dwelling.attributes['elec_no_gas_p'] ))
		print('district_no_gas_p  = ' + str(dwelling.attributes['district_no_gas_p'] ))
		print('district_high_gas_p= ' + str(dwelling.attributes['district_high_gas_p'] ))

		print('gas_boiler_water_p = ' + str(gas_boiler_water_p) +'\n')

		# Block gas boiler
		block_heating_water_p = dwelling.attributes['block_heating_space_p']
