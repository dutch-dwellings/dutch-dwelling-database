import os
import sys
import unittest

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.insulation_module import InsulationModule
from modules.classes import Dwelling

from tests.utils import get_mock_connection

class TestInsulationModule(unittest.TestCase):

	def setUp(self):
		self.mock_connection = get_mock_connection(strict=False)
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
		self.assertEqual(dwelling.attributes['insulation_floor_r_dist'].p(3.5), 1)
		self.assertEqual(dwelling.attributes['insulation_window_r_dist'].p(1/1.65), 1)

	def test_uses_building_code_and_measures_for_buildings_after_2006_facade(self):
		# From 2006 and onwards,
		# we don't have the WoON data anymore,
		# so we use the building code.

		# Easy example with just two applicable
		# measure years (2018 and 2019).
		attributes = {
			'bouwjaar': 2008,
			'woningtype': 'vrijstaand'
		}
		dwelling = Dwelling(attributes, self.mock_connection)
		self.insulation_module.process(dwelling)

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

		self.assertAlmostEqual(dwelling.attributes['insulation_facade_r_dist'].mean, expected_facade_mean)
		self.assertAlmostEqual(dwelling.attributes['insulation_facade_r_dist'].p(2.5), 1 - p_facade_measure)

	def test_uses_building_code_and_measures_for_buildings_after_2006_roof(self):
		attributes = {
			'bouwjaar': 2008,
			'woningtype': 'vrijstaand'
		}
		dwelling = Dwelling(attributes, self.mock_connection)
		self.insulation_module.process(dwelling)

		p_r_29 = 11.4 / (11.4 + 14.5)
		p_r_34 = 14.5 / (11.4 + 14.5)
		p_r_33 = 10.2 / (10.2 + 11.8)
		p_r_38 = 11.8 / (10.2 + 11.8)

		p_roof_measure_2018 = 1.98 * 199784 / 7189902
		p_roof_measure_2019 = 1.98 * 246325 / 7261671
		p_roof_measure = p_roof_measure_2018 + p_roof_measure_2019

		expected_roof_mean = 2.5 + p_roof_measure_2018 * (2.9 * p_r_29 + 3.4 * p_r_34) + p_roof_measure_2019 * (3.3 * p_r_33 + 3.8 * p_r_38)

		self.assertAlmostEqual(dwelling.attributes['insulation_roof_r_dist'].mean, expected_roof_mean)
		self.assertAlmostEqual(dwelling.attributes['insulation_roof_r_dist'].p(2.5), 1 - p_roof_measure)

	def test_uses_building_code_and_measures_for_buildings_after_2006_windows(self):
		attributes = {
			'bouwjaar': 2008,
			'woningtype': 'vrijstaand'
		}
		dwelling = Dwelling(attributes, self.mock_connection)
		self.insulation_module.process(dwelling)

		# WINDOWS
		# base value: not from the building code,
		# but for double glazing: 0.333
		p_window_measure_2018 = 1.98 * 312337 / 7189902
		p_window_measure_2019 = 1.98 * 376869 / 7261671
		p_window_measure = p_window_measure_2018 + p_window_measure_2019
		expected_window_mean = (1 - p_window_measure) * 0.333 + p_window_measure * (0.5 + 0.625)/2

		self.assertAlmostEqual(dwelling.attributes['insulation_window_r_dist'].mean, expected_window_mean)
		self.assertAlmostEqual(dwelling.attributes['insulation_window_r_dist'].p(0.333), 1 - p_window_measure)


	def test_uses_woon_data_and_measures_for_buildings_before_2006(self):
		# no cavity wall
		attributes = {
			'bouwjaar': 1919,
			'woningtype': 'vrijstaand'
		}
		# FACADE
		# Applicable WoON distribution:
		#	0.36: 0.018,
		#	0.43: 0.469,
		# ...
		p_multiplier = 1.98
		# For dwellings built in or before 2000, all measure years
		# from 2010 to 2019 are applicable.
		p_facade_measure_base_before_2000 = 35838 / 6591218 + 73097 / 6669286 + 76480 / 6739330 + 60548 / 6804459 + 84501 / 6870704 + 74448 / 6943943 + 75802 / 7027060 + 85442 / 7109692 + 100978 / 7189902 + 125197 / 7261671
		p_facade_measure = p_multiplier * p_facade_measure_base_before_2000

		dwelling = Dwelling(attributes, self.mock_connection)
		self.insulation_module.process(dwelling)

		# R-value is 0.36 if it was 0.36 to begin with (p=0.469)
		# and no measures were taken after that (p = 1 - p_measure).
		self.assertAlmostEqual(dwelling.attributes['insulation_facade_r_dist'].p(0.36), 0.018 * (1 - p_facade_measure), places=4)

		p_roof_measure_base_before_2000 = 115398 / 6591218 + 157347 / 6669286 + 195420 / 6739330 + 124267 / 6804459 + 155099 / 6870704 + 148447 / 6943943 + 148100 / 7027060 + 164024 / 7109692 + 199784 / 7189902 + 246325 / 7261671
		p_roof_measure = p_multiplier * p_roof_measure_base_before_2000
		self.assertAlmostEqual(dwelling.attributes['insulation_roof_r_dist'].p(0.39), 0.025 * (1 - p_roof_measure), places=4)

	def test_cavity_walls(self):
		# with cavity wall
		attributes = {
			'bouwjaar': 1920,
			'woningtype': 'vrijstaand'
		}
		p_multiplier = 1.98
		dwelling = Dwelling(attributes, self.mock_connection)

		cavity_wall_dist = self.insulation_module.process_insulation_type(dwelling, 'cavity wall')

		eligible_dwellings_cavity_wall_n = 3273065
		measure_n = 76784 + 114914 + 117197 + 96150 + 131324 + 132769 + 159507 + 159080 + 214035 + 281276
		p_measure = p_multiplier * measure_n / eligible_dwellings_cavity_wall_n

		self.assertEqual(cavity_wall_dist.p((1.25, 2.175)), p_measure)

		# without cavity wall
		attributes = {
			'bouwjaar': 1919,
			'woningtype': 'vrijstaand'
		}
		dwelling = Dwelling(attributes, self.mock_connection)
		cavity_wall_dist = self.insulation_module.process_insulation_type(dwelling, 'cavity wall')
		self.assertEqual(cavity_wall_dist.mean, 0)

		# with recent (probably already insulated) cavity wall
		attributes = {
			'bouwjaar': 2020,
			'woningtype': 'vrijstaand'
		}
		dwelling = Dwelling(attributes, self.mock_connection)
		cavity_wall_dist = self.insulation_module.process_insulation_type(dwelling, 'cavity wall')
		self.assertEqual(cavity_wall_dist.mean, 0)

	def test_facade_includes_cavity_wall_values(self):
		# has cavity wall
		attributes = {
			'bouwjaar': 1920,
			'woningtype': 'vrijstaand'
		}
		# FACADE
		# Applicable WoON distribution:
		# 	2.11: 0.548,
		# ...
		p_multiplier = 1.98
		# For dwellings built in or before 2000, all measure years
		# from 2010 to 2019 are applicable.
		p_facade_measure_base_before_2000 = 35838 / 6591218 + 73097 / 6669286 + 76480 / 6739330 + 60548 / 6804459 + 84501 / 6870704 + 74448 / 6943943 + 75802 / 7027060 + 85442 / 7109692 + 100978 / 7189902 + 125197 / 7261671
		p_facade_measure = p_multiplier * p_facade_measure_base_before_2000

		eligible_dwellings_cavity_wall_n = 3273065
		cavity_measure_n = 76784 + 114914 + 117197 + 96150 + 131324 + 132769 + 159507 + 159080 + 214035 + 281276
		p_cavity_measure = p_multiplier * cavity_measure_n / eligible_dwellings_cavity_wall_n

		dwelling = Dwelling(attributes, self.mock_connection)
		self.insulation_module.process(dwelling)

		# R-value is 2.11 if it was 2.11 to begin with (p=00.548)
		# and no measures were taken after that.
		self.assertAlmostEqual(dwelling.attributes['insulation_facade_r_dist'].p(2.11), 0.548 * (1 - p_facade_measure) * (1-p_cavity_measure))

	def test_saves_calculated_values(self):
		attributes = {
			'bouwjaar': 1920,
			'woningtype': 'vrijstaand'
		}
		dwelling1 = Dwelling(attributes, self.mock_connection)
		# identical dwelling
		dwelling2 =  Dwelling(attributes, self.mock_connection)

		self.insulation_module.process(dwelling1)
		# We monkeypatch the method,
		# to see if it is called.
		# If it is, it will fail with a TypeError.
		self.insulation_module.process_insulation_type = lambda x, y: None
		try:
			self.insulation_module.process(dwelling2)
		except TypeError as e:
			self.fail(f'Should not rise TypeError "{e}"')
