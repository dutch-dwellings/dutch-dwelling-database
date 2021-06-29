import os
import sys
import unittest

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.sampling_module import SamplingModule
from modules.classes import Dwelling
from utils.probability_utils import ProbabilityDistribution

from tests.utils import get_mock_connection

class TestSamplingModule(unittest.TestCase):

	def setUp(self):
		self.mock_connection = get_mock_connection()
		self.sampling_module = SamplingModule(self.mock_connection, silent=True)

	def test_can_sample_boolean(self):
		attributes = {
			'example_p': 1
		}
		dwelling = Dwelling(attributes, self.mock_connection)

		dwelling.outputs = {
			'example': {
				'type': 'boolean',
				'sampling': True,
				'distribution': 'example_p'
			}
		}

		self.sampling_module.process(dwelling)
		self.assertTrue(dwelling.attributes['example'])

	def test_can_sample_distribution(self):
		attributes = {
			'example_p': ProbabilityDistribution({
					1: 0.5,
					2: 0.5
				})
		}
		dwelling = Dwelling(attributes, self.mock_connection)

		dwelling.outputs = {
			'example': {
				'type': 'double precision',
				'sampling': True,
				'distribution': 'example_p'
			}
		}
		self.sampling_module.process(dwelling)
		# Should take mean by default
		self.assertAlmostEqual(dwelling.attributes['example'], 1.5)

	def test_can_sample_range(self):
		attributes = {
			'example_p': ProbabilityDistribution({
					 0: 0.01,
					 1: 0.01,
					 2.006: 0.01,
					 3: 0.01,
					 4: 0.01,
					 5: 0.01,
					 6: 0.88,
					 7: 0.01,
					 8: 0.01,
					 9: 0.01,
					10: 0.01,
					11: 0.01,
					12: 0.01,
				})
		}
		dwelling = Dwelling(attributes, self.mock_connection)

		dwelling.outputs = {
			'example': {
				'type': 'numrange',
				'sampling': True,
				'distribution': 'example_p'
			}
		}
		self.sampling_module.process(dwelling)
		# Should take 95% interval by default,
		# should round to 2 decimals.
		self.assertEqual(str(dwelling.attributes['example']), '[2.01, 10]')
