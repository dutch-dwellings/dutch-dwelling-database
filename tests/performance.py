import os
import sys
import unittest

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_utils import get_connection
from modules.gas_space_heating_module import GasSpaceHeatingModule


class TestPerformance(unittest.TestCase):

	def test_gas_boiler_module_performance(self):
		print('init')
		connection = get_connection()
		gas_boiler_module = GasBoilerModule(connection)
		print('done')
