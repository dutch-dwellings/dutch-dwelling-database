import os
import sys
import unittest
from unittest.mock import Mock

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.classes import PlaceholderDwelling, Region, PC6, Buurt

from tests.utils import get_mock_connection

class TestRegion(unittest.TestCase):

	def test_can_save_dwellings(self):
		region = Region()
		self.assertTrue(hasattr(region, 'dwellings'))
		self.assertEqual(region.dwellings, [])

class TestPC6(unittest.TestCase):

	def setUp(self):
		query_dict = {
			("SELECT vbo_id FROM bag WHERE pc6 = %s", '1000AA'): [
				("0363010000000001"),
				("0363010000000002"),
				("0363010000000003"),
				("0363010000000004"),
				("0363010000000005")
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
			("SELECT vbo_id FROM bag WHERE buurt_id = %s", 'BU00000000'): [
				("0363010000000006"),
				("0363010000000007"),
				("0363010000000008"),
				("0363010000000009"),
				("0363010000000010")
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
