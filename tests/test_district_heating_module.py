import os
import sys
import unittest
from unittest.mock import Mock

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.district_heating_module import DistrictHeatingModule
from pipeline import Dwelling

# We need to mock the connection to the database,
# so we can manipulate the query results.
mock_connection = Mock()
mock_cursor = Mock()
mock_connection.cursor.return_value = mock_cursor

def mock_cursor_execute(query, values=None):
	if query == "SELECT buurt_code, percentage_stadsverwarming FROM rvo_warmtenetten;":
		mock_cursor.fetchall.return_value = [('BU0001', 50), ('BU0002', 10)]
	else:
		pass
mock_cursor.execute = mock_cursor_execute


class TestDistrictHeatingModule(unittest.TestCase):

	def setUp(self):
		self.district_heating_module = DistrictHeatingModule(mock_connection)

	def test_neighbourhood_with_district_heating(self):
		# Dwelling in a neighbourhood with district_heating
		dwelling = Dwelling({'buurt_id': 'BU0001'}, mock_connection)
		self.district_heating_module.process(dwelling)
		self.assertEqual(dwelling.attributes['district_heating_p'], 0.5)

	def test_neighbourhood_without_district_heating(self):
		# Dwelling in a neighbourhood without district_heating
		dwelling = Dwelling({'buurt_id': 'BU0003'}, mock_connection)
		self.district_heating_module.process(dwelling)
		self.assertEqual(dwelling.attributes['district_heating_p'], 0)

if __name__ == '__main__':
	unittest.main()
