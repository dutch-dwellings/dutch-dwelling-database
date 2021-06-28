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

	def test_uses_building_code_for_new_buildings(self):
		attributes = {
			'bouwjaar': 2020,
			'woningtype': 'vrijstaand'
		}
		dwelling = Dwelling(attributes, self.mock_connection)
		self.insulation_module.process(dwelling)

		self.assertEqual(dwelling.attributes['insulation_facade_r_dist'].p(4.5), 1)
		self.assertEqual(dwelling.attributes['insulation_roof_r_dist'].p(6), 1)
		# self.assertEqual(dwelling.attributes['insulation_wall_r_dist'].p(3.5), 1)
		# self.assertEqual(dwelling.attributes['insulation_window_r_dist'].p(1/1.65), 1)

	def test_uses_building_code_and_measures_for_buildings_after_2006(self):
		# From 2006 and onwards,
		# we don't have the WoON data anymore,
		# so we use the building code.

		# Easy example with just two applicable
		# measure years (2018 and 2019).
		attributes = {
			'bouwjaar': 2008,
			'woningtype': 'vrijstaand'
		}
		# FACADE
		# Applicable building code:
		# 2003: 2.5
		# Measures R-value:
		# 2018:
		#	2.9: 11.4 / (11.4 + 14.5)
		#	3.4: 14.5 / (11.4 + 14.5)
		# 2019:
		#	3.3: 10.2 / (10.2 + 11.8)
		#	3.8: 11.8 / (10.2 + 11.8)
		# Measures prob:
		#	multiplier: 1.98
		#	2018 measures: 100978
		#	2019 measures: 125197
		#	dwellings until 2008: 7189902
		#	dwellings until 2009: 7261671
		p_facade_measure_2018 = 1.98 * 100978 / 7189902 # ~ 2.8%
		p_facade_measure_2019 = 1.98 * 125197 / 7261671 # ~ 3.4%
		p_facade_measure = p_facade_measure_2018 + p_facade_measure_2019

		p_r_29 = 11.4 / (11.4 + 14.5)
		p_r_34 = 14.5 / (11.4 + 14.5)
		p_r_33 = 10.2 / (10.2 + 11.8)
		p_r_38 = 11.8 / (10.2 + 11.8)

		expected_facade_mean = 2.5 + p_facade_measure_2018 * (2.9 * p_r_29 + 3.4 * p_r_34) + p_facade_measure_2019 * (3.3 * p_r_33 + 3.8 * p_r_38)

		dwelling = Dwelling(attributes, self.mock_connection)
		self.insulation_module.process(dwelling)

		self.assertAlmostEqual(dwelling.attributes['insulation_facade_r_dist'].mean, expected_facade_mean)
		self.assertAlmostEqual(dwelling.attributes['insulation_facade_r_dist'].p(2.5), 1 - p_facade_measure)

		p_roof_measure_2018 = 1.98 * 199784 / 7189902
		p_roof_measure_2019 = 1.98 * 246325 / 7261671
		p_roof_measure = p_roof_measure_2018 + p_roof_measure_2019

		expected_roof_mean = 2.5 + p_roof_measure_2018 * (2.9 * p_r_29 + 3.4 * p_r_34) + p_roof_measure_2019 * (3.3 * p_r_33 + 3.8 * p_r_38)

		self.assertAlmostEqual(dwelling.attributes['insulation_roof_r_dist'].mean, expected_roof_mean)
		self.assertAlmostEqual(dwelling.attributes['insulation_roof_r_dist'].p(2.5), 1 - p_roof_measure)

	def test_uses_woon_data_and_measures_for_buildings_before_2006(self):
		# no cavity wall
		attributes = {
			'bouwjaar': 1919,
			'woningtype': 'vrijstaand'
		}
		# FACADE
		# Applicable WoON distribution:
		# 	0.36: 0.3%
		# 	0.43: 7.5%
		# ...
		p_multiplier = 1.98
		# For dwellings built in or before 2000, all measure years
		# from 2010 to 2019 are applicable.
		p_facade_measure_base_before_2000 = 35838 / 6591218 + 73097 / 6669286 + 76480 / 6739330 + 60548 / 6804459 + 84501 / 6870704 + 74448 / 6943943 + 75802 / 7027060 + 85442 / 7109692 + 100978 / 7189902 + 125197 / 7261671
		p_facade_measure = p_multiplier * p_facade_measure_base_before_2000

		dwelling = Dwelling(attributes, self.mock_connection)
		self.insulation_module.process(dwelling)

		# R-value is 0.43 if it was 0.43 to begin with (p=0.075)
		# and no measures were taken after that (p = 1 - p_measure).
		self.assertAlmostEqual(dwelling.attributes['insulation_facade_r_dist'].p(0.43), 0.075 * (1 - p_facade_measure))

		p_roof_measure_base_before_2000 = 115398 / 6591218 + 157347 / 6669286 + 195420 / 6739330 + 124267 / 6804459 + 155099 / 6870704 + 148447 / 6943943 + 148100 / 7027060 + 164024 / 7109692 + 199784 / 7189902 + 246325 / 7261671
		p_roof_measure = p_multiplier * p_roof_measure_base_before_2000
		self.assertAlmostEqual(dwelling.attributes['insulation_roof_r_dist'].p(0.39), 0.025 * (1 - p_roof_measure))
