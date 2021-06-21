import os
import sys
import unittest

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils import get_mock_connection

from modules.base_module import BaseModule
from modules.classes import Dwelling

class TestBaseModule(unittest.TestCase):

	def setUp(self):
		vbo_id = '0363010000000001'
		attributes = {
			'vbo_id': vbo_id
		}
		self.mock_connection = get_mock_connection()
		self.dwelling = Dwelling(attributes, self.mock_connection)
		self.base_module = BaseModule(self.mock_connection, silent=True)


		class ChildrenModule(BaseModule):

			def process(self, dwelling):
				continue_processing = super().process(dwelling)
				# Dwelling has already been processed by this module
				if not continue_processing:
					return
				dwelling.attributes['child_attribute'] = 'foobar'

		self.children_module = ChildrenModule(self.mock_connection, silent=True)

	def test_adds_processed_by_to_dwelling(self):
		self.assertEqual(self.dwelling.processed_by, [])
		self.base_module.process(self.dwelling)
		self.assertEqual(self.dwelling.processed_by, ['BaseModule'])

	def test_processed_by_doesnt_override(self):
		self.base_module.process(self.dwelling)
		self.children_module.process(self.dwelling)
		self.assertEqual(self.dwelling.processed_by, ['BaseModule', 'ChildrenModule'])

	def test_skips_processing_when_dwelling_already_seen(self):
		self.dwelling.processed_by = ['ChildrenModule']
		self.children_module.process(self.dwelling)
		self.assertEqual(self.dwelling.processed_by, ['ChildrenModule'])
		self.assertNotIn('child_attribute', self.dwelling.attributes)
