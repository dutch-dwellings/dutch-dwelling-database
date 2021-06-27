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

if __name__ == '__main__':
	unittest.main()
