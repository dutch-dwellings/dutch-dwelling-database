from functools import partial
import os
import sys
import unittest
from unittest.mock import Mock

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.classes import Dwelling, PlaceholderDwelling, Region, PC6, Buurt

from tests.utils import get_mock_connection

class TestRegion(unittest.TestCase):

	def setUp(self):
		self.region = Region()
		self.connection = get_mock_connection()
		self.vbo_id = '0363010000000001'
		self.placeholder_attributes = {'vbo_id': self.vbo_id}
		self.placeholder_dwelling = PlaceholderDwelling(self.placeholder_attributes, self.connection)
		self.region.dwellings.append(self.placeholder_dwelling)

	def test_can_save_dwellings(self):
		region = Region()
		self.assertTrue(hasattr(region, 'dwellings'))
		self.assertEqual(region.dwellings, [])

	def test_can_replace_placeholders(self):
		# dwelling with same vbo_id as placeholder
		attributes = self.placeholder_attributes.copy()
		dwelling = Dwelling(attributes, self.connection)

		self.region.add_dwelling(dwelling)
		# placeholder has been replaced
		self.assertEqual(self.region.dwellings, [dwelling])

	def test_raises_when_adding_dwelling_outside_region(self):
		# dwelling with vbo_id that is not inside that region
		attributes = {'vbo_id': '0363010000000002'}
		dwelling = Dwelling(attributes, self.connection)

		add_dwelling_partial = partial(self.region.add_dwelling, dwelling)
		self.assertRaises(ValueError, add_dwelling_partial)

	def test_raises_when_adding_existing_dwelling(self):
		attributes_1 = {'vbo_id': '0363010000000002'}
		dwelling_1 = Dwelling(attributes_1, self.connection)
		attributes_2 = attributes_1.copy()
		dwelling_2 = Dwelling(attributes_2, self.connection)

		self.region.dwellings = [dwelling_1]
		# Attempt to add the same dwelling.
		add_dwelling_partial = partial(self.region.add_dwelling, dwelling_2)

		self.assertRaises(ValueError, add_dwelling_partial)

	def test_updates_dwelling_with_placeholder_dwelling_values_when_adding(self):
		self.placeholder_dwelling.attributes['foo'] = 'bar'

		# dwelling with same vbo_id as placeholder
		attributes = {'vbo_id': self.vbo_id}
		dwelling = Dwelling(attributes, self.connection)

		self.region.add_dwelling(dwelling)
		self.assertEqual(dwelling.attributes['foo'], 'bar')

	def test_raises_when_adding_dwelling_with_conflicting_information(self):
		self.placeholder_dwelling.attributes['foo'] = 'bar'

		# dwelling with same vbo_id as placeholder
		attributes = {'vbo_id': self.vbo_id, 'foo': 'spam'}
		dwelling = Dwelling(attributes, self.connection)

		add_dwelling_partial = partial(self.region.add_dwelling, dwelling)
		self.assertRaises(ValueError, add_dwelling_partial)

class TestPC6(unittest.TestCase):

	def setUp(self):
		query_dict = {
			("SELECT vbo_id FROM bag WHERE pc6 = %s", ('1000AA',)): [
				("0363010000000001",),
				("0363010000000002",),
				("0363010000000003",),
				("0363010000000004",),
				("0363010000000005",)
			]
		}
		self.mock_connection = get_mock_connection(query_dict)

	def test_can_save_dwellings(self):
		pc6 = PC6('1000AA', [], self.mock_connection)
		self.assertTrue(hasattr(pc6, 'dwellings'))
		self.assertIsInstance(pc6.dwellings, list)

	def test_populates_dwellings_with_placeholders(self):
		pc6 = PC6('1000AA', [], self.mock_connection)
		self.assertTrue(len(pc6.dwellings) > 0)
		dwelling = pc6.dwellings[0]
		self.assertIsInstance(dwelling, PlaceholderDwelling)

class TestBuurt(unittest.TestCase):

	def setUp(self):
		query_dict = {
			("SELECT vbo_id FROM bag WHERE buurt_id = %s", ('BU00000000',)): [
				("0363010000000006",),
				("0363010000000007",),
				("0363010000000008",),
				("0363010000000009",),
				("0363010000000010",)
			]
		}
		self.mock_connection = get_mock_connection(query_dict)

	def test_can_save_dwellings(self):
		buurt = Buurt('BU00000000', [], self.mock_connection)
		self.assertTrue(hasattr(buurt, 'dwellings'))
		self.assertIsInstance(buurt.dwellings, list)

	def test_populates_dwellings_with_placeholders(self):
		buurt = Buurt('BU00000000', [], self.mock_connection)
		self.assertTrue(len(buurt.dwellings) > 0)
		dwelling = buurt.dwellings[0]
		self.assertIsInstance(dwelling, PlaceholderDwelling)
