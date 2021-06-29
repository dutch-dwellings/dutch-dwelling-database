import os
import sys
import unittest

import numpy as np

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils import get_mock_connection

from modules.classes import Dwelling, PC6
from modules.energy_label_module import EnergyLabelModule, EnergyLabelRegionalModule

class TestEnergyLabelModule(unittest.TestCase):

	def setUp(self):
		query_dict = {
			('SELECT vbo_id FROM bag WHERE pc6 = %s', ('1000AA',)): [],
			('SELECT energieklasse FROM energy_labels WHERE energieklasse IS NOT null AND vbo_id = %s', ('0003010000000001',)): []
		}
		self.connection = get_mock_connection(query_dict)
		self.energy_label_module = EnergyLabelModule(self.connection, silent=True)

	def test_predicts_epi(self):
		attributes = {
			'vbo_id': '0003010000000001',
			'bouwjaar': 2020,
			'woningtype': 'tussenwoning'
		}
		dwelling = Dwelling(attributes, self.connection)

		pc6 = PC6('1000AA', [], self.connection)
		pc6.attributes['epi_log_pc6_average'] = 0.1823215568
		dwelling.regions['pc6'] = pc6

		self.energy_label_module.process(dwelling)
		self.assertAlmostEqual(dwelling.attributes['energy_label_epi_mean'], 1.1123215698960702)
		self.assertEqual(dwelling.attributes['energy_label_epi_95'], (0.7219813995163725, 1.7136996544299485))
		self.assertEqual(dwelling.attributes['energy_label_class_mean'], 'B')
		self.assertEqual(dwelling.attributes['energy_label_class_95'], ('A', 'D'))

class TestEnergyLabelRegionalModule(unittest.TestCase):

	def setUp(self):
		query_dict = {
			('SELECT vbo_id FROM bag WHERE pc6 = %s', ('1000AA',)): [('0003010000000001',), ('0003010000000002',), ('0003010000000003',)],
			('SELECT AVG(LN(epi_imputed)) FROM energy_labels WHERE pc6 = %s', ('1000AA',)): [(0.5,)]
		}
		self.connection = get_mock_connection(query_dict)
		self.energy_label_regional_module = EnergyLabelRegionalModule(self.connection, silent=True)
		self.pc6 = PC6('1000AA', [self.energy_label_regional_module], self.connection)

	def test_gets_average_log_of_epi_imputed(self):
		self.assertEqual(self.pc6.attributes['epi_log_pc6_average'], 0.5)
