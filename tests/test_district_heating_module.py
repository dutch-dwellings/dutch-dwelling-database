import os
import sys
import unittest

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.district_space_heating_module import DistrictSpaceHeatingModule
from pipeline import Dwelling

from tests.utils import get_mock_connection

@unittest.skip('Implementation has changed...')
class TestDistrictSpaceHeatingModule(unittest.TestCase):

	def setUp(self):
		self.mock_connection = get_mock_connection({"SELECT buurt_code, percentage_stadsverwarming FROM rvo_warmtenetten;": [('BU0001', 50), ('BU0002', 10)]})
		self.district_heating_module = DistrictSpaceHeatingModule(mock_connection)

	def test_neighbourhood_with_district_heating(self):
		# Dwelling in a neighbourhood with district_heating
		dwelling = Dwelling({'buurt_id': 'BU0001'}, self.mock_connection)
		self.district_heating_module.process(dwelling)
		self.assertEqual(dwelling.attributes['district_heating_space_p'], 0.5)

	def test_neighbourhood_without_district_heating(self):
		# Dwelling in a neighbourhood without district_heating
		dwelling = Dwelling({'buurt_id': 'BU0003'}, self.mock_connection)
		self.district_heating_module.process(dwelling)
		self.assertEqual(dwelling.attributes['district_heating_space_p'], 0)

if __name__ == '__main__':
	unittest.main()
