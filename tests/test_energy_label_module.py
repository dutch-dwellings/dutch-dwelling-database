import math
import os
import sys
import unittest
from unittest.mock import patch

import numpy as np

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils import get_mock_connection

from modules.classes import Dwelling, PC6, Buurt
from modules.energy_label_module import EnergyLabelModule, EnergyLabelPredictionModule, EnergyLabelRegionalModule

class TestEnergyLabelModule(unittest.TestCase):

	def setUp(self):
		query_dict = {
			('SELECT energieklasse, epi_imputed FROM energy_labels WHERE energieklasse IS NOT null AND epi_imputed > 0 AND vbo_id = %s', ('0003010000000001',)): [('A', 0.7)],
			('SELECT energieklasse, epi_imputed FROM energy_labels WHERE energieklasse IS NOT null AND epi_imputed > 0 AND vbo_id = %s', ('0003010000000002',)): []
		}
		self.connection = get_mock_connection(query_dict)
		self.energy_label_module = EnergyLabelModule(self.connection, silent=True)

	def test_gets_both_energy_label_class_and_epi_imputed(self):
		dwelling = Dwelling({'vbo_id': '0003010000000001'}, self.connection)
		self.energy_label_module.process(dwelling)
		self.assertEqual(dwelling.attributes['energy_label_class'], 'A')
		self.assertEqual(dwelling.attributes['energy_label_epi'], 0.7)

	def test_sets_to_none_when_no_label(self):
		dwelling = Dwelling({'vbo_id': '0003010000000002'}, self.connection)
		self.energy_label_module.process(dwelling)
		self.assertEqual(dwelling.attributes['energy_label_class'], None)
		self.assertEqual(dwelling.attributes['energy_label_epi'], None)

class TestEnergyLabelPredictionModule(unittest.TestCase):

	@patch('modules.energy_label_module.register_range')
	def setUp(self, register_range_mock):
		query_dict = {
			('SELECT vbo_id FROM bag WHERE pc6 = %s', ('1000AA',)): [],
			('SELECT energieklasse, epi_imputed FROM energy_labels WHERE energieklasse IS NOT null AND epi_imputed > 0 AND vbo_id = %s', ('0003010000000001',)): [('A', 0.7)],
			('SELECT energieklasse, epi_imputed FROM energy_labels WHERE energieklasse IS NOT null AND epi_imputed > 0 AND vbo_id = %s', ('0003010000000002',)): [('B', 1.2)],
			('SELECT energieklasse, epi_imputed FROM energy_labels WHERE energieklasse IS NOT null AND epi_imputed > 0 AND vbo_id = %s', ('0003010000000003',)): [],
			('SELECT vbo_id FROM bag WHERE buurt_id = %s', ('BU0000000',)): [('0003010000000001',), ('0003010000000002',), ('0003010000000003',)]
		}
		self.connection = get_mock_connection(query_dict, strict=False)
		self.energy_label_prediction_module = EnergyLabelPredictionModule(self.connection, silent=True)
		self.energy_label_module = EnergyLabelModule(self.connection, silent=True)
		self.energy_label_regional_module = EnergyLabelRegionalModule(self.connection, silent=True)
		self.energy_label_class_range_mock = self.energy_label_prediction_module.EnergyLabelClassRange

	def test_predicts_epi(self):
		attributes = {
			'vbo_id': '0003010000000001',
			'bouwjaar': 2020,
			'woningtype': 'tussenwoning'
		}
		dwelling = Dwelling(attributes, self.connection)

		pc6 = PC6('1000AA', self.connection)
		pc6.attributes['energy_label_epi_log_avg'] = 0.1823215568
		dwelling.regions['pc6'] = pc6

		self.energy_label_prediction_module.process(dwelling)
		self.assertAlmostEqual(dwelling.attributes['energy_label_epi_mean'], 1.1123215698958466, places=3)
		epi_interval = dwelling.attributes['energy_label_epi_95']
		self.assertAlmostEqual(epi_interval.lower, 0.7336717114532558)
		self.assertAlmostEqual(epi_interval.upper, 1.6873401901864706)
		self.assertEqual(dwelling.attributes['energy_label_class_mean'], 'B')
		# A bit of an indirect way to check that this is the EnergyLabelClassRange
		# from D to A.
		self.energy_label_class_range_mock.assert_called_with('D', 'A', bounds='[]')

	def test_uses_average_of_buurt_when_no_labels_in_pc6(self):
		pc6 = PC6('1000AA', self.connection)
		# No average this time
		pc6.attributes['energy_label_epi_log_avg'] = None

		buurt = Buurt('BU0000000', self.connection)
		buurt.attributes['energy_label_epi_log_avg'] = 0.1823215568

		attributes = {
			'vbo_id': '0003010000000001',
			'bouwjaar': 2020,
			'woningtype': 'tussenwoning'
		}
		dwelling = Dwelling(attributes, self.connection)
		dwelling.regions['pc6'] = pc6
		dwelling.regions['buurt'] = buurt

		self.energy_label_prediction_module.process(dwelling)

		self.energy_label_prediction_module.process(dwelling)
		# Should be the same as previous calculation.
		self.assertAlmostEqual(dwelling.attributes['energy_label_epi_mean'], 1.1123215698958466, places=3)

	def test_uses_national_average_when_no_other_averages(self):
		pc6 = PC6('1000AA', self.connection)
		# No average this time
		pc6.attributes['energy_label_epi_log_avg'] = None

		buurt = Buurt('BU0000000', self.connection)
		buurt.attributes['energy_label_epi_log_avg'] = None

		attributes = {
			'vbo_id': '0003010000000001',
			'bouwjaar': 2020,
			'woningtype': 'tussenwoning'
		}
		dwelling = Dwelling(attributes, self.connection)
		dwelling.regions['pc6'] = pc6
		dwelling.regions['buurt'] = buurt

		self.energy_label_prediction_module.process(dwelling)
		# Exact value doesn't matter, but that it is different
		# from previous results is.
		self.assertTrue(dwelling.attributes['energy_label_epi_mean'] > 1.12)

class TestEnergyLabelRegionalModule(unittest.TestCase):

	def setUp(self):
		query_dict = {
			('SELECT vbo_id FROM bag WHERE pc6 = %s', ('1000AA',)): [('0003010000000001',), ('0003010000000002',), ('0003010000000003',)],
			('SELECT vbo_id FROM bag WHERE pc6 = %s', ('9999XX',)): [('0003010000000004',), ('0003010000000005',), ('0003010000000006',)],
			('SELECT AVG(LN(epi_imputed)) FROM energy_labels WHERE pc6 = %s AND epi_imputed > 0', ('1000AA',)): [(0.5,)],
			('SELECT AVG(LN(epi_imputed)) FROM energy_labels WHERE pc6 = %s AND epi_imputed > 0', ('9999XX',)): [(None,)],
			('SELECT vbo_id FROM bag WHERE buurt_id = %s', ('BU0000000',)): [('0003010000000001',), ('0003010000000002',), ('0003010000000003',)],
			('SELECT vbo_id FROM bag WHERE buurt_id = %s', ('BU0000001',)): [],
			('SELECT energieklasse, epi_imputed FROM energy_labels WHERE energieklasse IS NOT null AND epi_imputed > 0 AND vbo_id = %s', ('0003010000000001',)): [('A', 0.7)],
			('SELECT energieklasse, epi_imputed FROM energy_labels WHERE energieklasse IS NOT null AND epi_imputed > 0 AND vbo_id = %s', ('0003010000000002',)): [('B', 1.2)],
			('SELECT energieklasse, epi_imputed FROM energy_labels WHERE energieklasse IS NOT null AND epi_imputed > 0 AND vbo_id = %s', ('0003010000000003',)): []
		}
		self.connection = get_mock_connection(query_dict)
		self.energy_label_regional_module = EnergyLabelRegionalModule(self.connection, silent=True)
		self.energy_label_module = EnergyLabelModule(self.connection, silent=True)

	def test_gets_average_log_of_epi_imputed_pc6(self):
		pc6 = PC6('1000AA', self.connection, pc6_modules=[self.energy_label_regional_module])
		self.assertEqual(pc6.attributes['energy_label_epi_log_avg'], 0.5)

	def test_gets_average_log_of_epi_imputed_buurt(self):
		buurt = Buurt('BU0000000', self.connection, buurt_modules=[self.energy_label_regional_module], buurt_dwelling_modules=[self.energy_label_module])
		expected_avg = (math.log(0.7) + math.log(1.2)) / 2
		self.assertAlmostEqual(buurt.attributes['energy_label_epi_log_avg'], expected_avg)

	def test_sets_buurt_avg_to_none_when_no_labels(self):
		buurt = Buurt('BU0000001', self.connection, buurt_modules=[self.energy_label_regional_module], buurt_dwelling_modules=[self.energy_label_module])
		self.assertEqual(buurt.attributes['energy_label_epi_log_avg'], None)

