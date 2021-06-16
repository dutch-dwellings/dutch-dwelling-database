import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule

class EnergyLabelModule(BaseModule):

	def __init__(self, connection):
		super().__init__(connection)

	def create_dicts(self):
		self.buurten_verwarming_data = {}

	def get_energy_label(self, vbo_id):
		cursor = self.connection.cursor()
		# Get energy label of dwelling
		query = "SELECT energieklasse FROM energy_labels WHERE energieklasse IS NOT null AND vbo_id = %s"
		cursor.execute(query, (vbo_id,))
		results = cursor.fetchall()
		return results.pop().pop()
		cursor.close()

	def process(self, dwelling):
		super().process(dwelling)
		vbo_id = dwelling.attributes['vbo_id']
		buurt_id = dwelling.attributes['buurt_id']
		energy_label = self.get_energy_label(vbo_id)
		print(energy_label)
		dwelling.attributes['energy_label'] = energy_label
