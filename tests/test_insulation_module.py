import os
import sys
import unittest

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.insulation_module import InsulationModule
from modules.classes import Dwelling

from tests.utils import get_mock_connection

class TestDistrictSpaceHeatingModule(unittest.TestCase):

	def setUp(self):
		self.mock_connection = get_mock_connection()
		self.insulation_module = InsulationModule(self.mock_connection, silent=True)

	def test_uses_building_code_for_new_buildings_facade(self):
		attributes = {
			'bouwjaar': 2020,
			'woningtype': 'vrijstaand'
		}
		dwelling = Dwelling(attributes, self.mock_connection)
		self.insulation_module.process(dwelling)
		self.assertEqual(dwelling.attributes['insulation_facade_r_dist'].p(4.5), 1)

		# self.assertEqual(dwelling.attributes['insulation_roof_r_dist'].p(6), 1)
		# self.assertEqual(dwelling.attributes['insulation_wall_r_dist'].p(3.5), 1)
		# self.assertEqual(dwelling.attributes['insulation_window_r_dist'].p(1/1.65), 1)

	def test_uses_building_code_and_measures_for_buildings_after_1992_facade(self):
		# Easy example with just one applicable
		# measure year.
		attributes = {
			'bouwjaar': 2009,
			'woningtype': 'vrijstaand'
		}
		# FACADE
		# Applicable building code:
		# 2003: 2.5
		# Measures R-value:
		# 2019:
		#	3.3: 10.2 / (10.2 + 11.8)
		#	3.8: 11.8 / (10.2 + 11.8)
		# Measures prob:
		#	multiplier: 1.98
		#	measures: 125197
		#	dwellings until 2009: 7261671
		p_measure = 1.98 * 125197 / 7261671
		p_r_33 = 10.2 / (10.2 + 11.8)
		p_r_38 = 11.8 / (10.2 + 11.8)
		expected_mean = (1 - p_measure) * 2.5 + p_measure * (3.3 * p_r_33 + 3.8 * p_r_38)
		dwelling = Dwelling(attributes, self.mock_connection)
		self.insulation_module.process(dwelling)
		self.assertAlmostEqual(dwelling.attributes['insulation_facade_r_dist'].mean, expected_mean)
		self.assertAlmostEqual(dwelling.attributes['insulation_facade_r_dist'].p(2.5), 1 - p_measure)

if __name__ == '__main__':
	unittest.main()
