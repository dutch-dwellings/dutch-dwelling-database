import os
import sys
import unittest

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.energy_label_utils import label_to_epi, epi_to_label

class TestEnergyLabelsUtils(unittest.TestCase):

	def test_label_to_epi(self):
		self.assertEqual(label_to_epi('A'), 0.938)
		self.assertEqual(label_to_epi('A+++++'), 0.281)
		self.assertEqual(label_to_epi('G'), 3.237)

	def test_epi_to_label(self):
		# check for within ranges
		self.assertEqual(epi_to_label(0.938), 'A')
		self.assertEqual(epi_to_label(0.281), 'A++')
		# check for extreme values
		self.assertEqual(epi_to_label(-10), 'A++')
		self.assertEqual(epi_to_label(10), 'G')
		# check for boundaries
		self.assertEqual(epi_to_label(1.3), 'B')
		self.assertEqual(epi_to_label(1.300001), 'C')

