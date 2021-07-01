import os
import sys

import folium
from folium.plugins import BeautifyIcon, Fullscreen
from psycopg2.extras import DictCursor
from pyproj import Proj, transform

# Required to import from root directory
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.database_utils import get_connection
from pipeline import main as pipeline

def parse_geometry(geometry):
	y_str, x_str = geometry.replace('{', '').replace('}', '').split(', ')
	return float(x_str), float(y_str)

def rijksdriehoek_to_wsg84(x, y):
	# solution from
	# https://publicwiki.deltares.nl/display/OET/Python+convert+coordinates

	# SR-ORG:6781 definition in
	# from http://spatialreference.org/ref/sr-org/6781/
	p1 = Proj("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 +units=m +no_defs")
	p2 = Proj(proj='latlong', datum='WGS84')

	lon, lat, z = transform(p1, p2, x, y, 0.0)
	return (lat, lon)

def initiate_folium_map(lon, lat):
	print('Creating map...')
	return folium.Map(location=(lon, lat), tiles='cartodb positron', zoom_start=17)

def get_buurt_results(buurt_id, cursor):

	query = '''
	SELECT
		bag.*, results.*, energy_labels.energieklasse as energy_label_class, wijken_en_buurten as buurt_name
	FROM
		results
	LEFT JOIN
		bag
	ON
		results.vbo_id = bag.vbo_id
	LEFT JOIN
		energy_labels
	ON
		energy_labels.vbo_id = bag.vbo_id
	LEFT JOIN
		cbs_84799ned_kerncijfers_wijken_en_buurten_2020
	ON
		bag.buurt_id = cbs_84799ned_kerncijfers_wijken_en_buurten_2020.area_code
	WHERE
		bag.buurt_id = %s
	'''

	print('Executing buurt query...')
	cursor.execute(query, (buurt_id,))
	return cursor

def get_bag_vbo(vbo_id, cursor):
	query = '''
	SELECT
		*
	FROM
		bag
	WHERE
		bag.vbo_id = %s
	'''

	print('Executing vbo query...')
	cursor.execute(query, (vbo_id,))
	return cursor.fetchone()

def get_energy_label_colour(dwelling):
	# extracted from 'energielabel-voorbeeld-woningen.pdf'
	energy_label_colours = {
		'A+++++': '#009037', # dark green
		 'A++++': '#009037', # dark green
		  'A+++': '#009037', # dark green
		   'A++': '#009037', # dark green
		    'A+': '#009037', # dark green
		     'A': '#009037', # dark green
		     'B': '#55ab26', # green
		     'C': '#c8d100', # light green
		     'D': '#ffec00', # yellow
		     'E': '#faba00', # orange
		     'F': '#eb6909', # light red
		     'G': '#e2001a'  # red
	}
	label_class = dwelling['energy_label_class']
	if label_class is None:
		label_class = dwelling['energy_label_class_mean']
	return energy_label_colours[label_class]

def add_markers_to_map(vbo_id, m, cursor):

	print('Iterating through results...')
	i = 0

	for dwelling in cursor:

		if dwelling['vbo_id'] == vbo_id:
			icon_type = 'house'
		else:
			icon_type = 'energy_label'

		add_dwelling_marker_to_map(m, dwelling, icon_type)

		i += 1

		print(f'\tprocessed: {i} ({dwelling["adres"]}) {" "*20}', end='\r')
	print('')

def add_dwelling_marker_to_map(m, dwelling, icon_type):
	x, y = parse_geometry(dwelling['geometry'])
	lon, lat = rijksdriehoek_to_wsg84(x, y)

	def percentage(key):
		return f'{dwelling[key] * 100:.1f}%'

	def numeric_range(key):
		mean = dwelling[f'{key}_mean']
		range_ = dwelling[f'{key}_95']

		if type(range_) == str:
			lower = range_.replace('[','').replace(']','').split(',')[0]
			upper = range_.replace('[','').replace(']','').split(',')[1]
			return f'{mean} (95%: {lower} to {upper})'
		else:
			lower = range_.lower
			upper = range_.upper
			return f'{mean:.1f} (95%: {lower:.1f} to {upper:.1f})'

	results = {
		'Base data': {
			'vbo ID': f"<samp>{dwelling['vbo_id']}</samp>",
			'coordinates': f'({lon:.2f}, {lat:.2f})',
			'construction year': dwelling['bouwjaar'],
			'surface area': f"{dwelling['oppervlakte']} m<sup>2</sup>",
			'dwelling type': f"{dwelling['woningtype'].replace('_', ' ')}",
			'neighbourhood': f"{dwelling['buurt_name']} (<samp>{dwelling['buurt_id']}</samp>)"
		},
		'Energy label': {
			'measured': dwelling['energy_label_class'],
			'predicted': numeric_range('energy_label_class')
		},

		'Space heating': {
			'district heating': percentage('district_heating_space_p'),
			'block heating': percentage('block_heating_space_p'),
			'gas boiler': percentage('gas_boiler_space_p'),
			'electric boiler': percentage('elec_boiler_space_p'),
			'hybrid heat pump': percentage('hybrid_heat_pump_p'),
			'electric heat pump': percentage('electric_heat_pump_p')
		},

		'Water heating': {
			'district heating': percentage('district_heating_water_p'),
			'block heating': percentage('block_heating_water_p'),
			'gas boiler': percentage('gas_boiler_water_p'),
			'electric boiler': percentage('elec_boiler_water_p'),
			'electric heat pump': percentage('electric_heat_pump_water_p')
		},

		'Cooking': {
			'gas': percentage('gas_cooking_p'),
			'electric': percentage('electric_cooking_p')
		},

		'Insulation': {
			'facade R': numeric_range('insulation_facade_r'),
			'roof R': numeric_range('insulation_roof_r'),
			'floor R': numeric_range('insulation_floor_r'),
			'windows R': numeric_range('insulation_window_r')
		}
	}

	table = '<table>'
	for key, val in results.items():

		for index, (key_2, val_2) in enumerate(val.items()):
			table += f'<tr class="{"new-cat" if index == 0 else ""}">\n'
			table += f'\t<td>{key if index == 0 else ""}</td>\n'
			table += f'\t<td>{key_2}</td>\n'
			table += f'\t<td>{val_2}</td>\n'
			table += '</tr>\n'
	table += '</table>'

	style = '''
	<style>
	* {
		font-size: 16px;
		font-family: -apple-system, BlinkMacSystemFont, sans-serif
	}
	td {
		padding-top: 5px;
		padding-right: 20px;
	}
	tr.new-cat > td {
		padding-top: 15px
	}
	td:nth-child(1) { font-weight: bold }
	td:nth-child(2) { font-weight: bold; text-align: right; }
	td:nth-child(3) { }
	</style>
	'''

	html = f'''
	{style}
	<div style="width: 45vw; height: 70vh; position: relative">
		<div style="border-bottom: 2px solid #ddd; margin-bottom: 10px">
			<h3>Dwelling: {dwelling['adres'].replace('_', ' ')}</h3>
		</div>
		<div style='overflow-y: auto; height: 90%'>
			{table}
		</div>
	</div>
	'''

	my_popup =  folium.Popup(html)
	if icon_type == 'house':
		icon = folium.Icon(icon='home', prefix='fa')
	else:
		icon = BeautifyIcon(
			icon_shape='circle-dot',
			border_color=get_energy_label_colour(dwelling),
			border_width=4,
		)

	folium.Marker((lon, lat), popup=my_popup, icon=icon).add_to(m)

def parse_multipolygon(multipolygon):
	coordinates_str = multipolygon.replace("MULTIPOLYGON (((", "").replace(")))", "").split(', ')

	def parse_coordinate(coordinate_str):
		x_str, y_str = coordinate_str.split(" ")
		x, y = float(x_str), float(y_str)
		lat, lon = rijksdriehoek_to_wsg84(x, y)
		# GeoJSON uses reverse ordering, confusingly...
		return [lon, lat]

	return [parse_coordinate(coord_str) for coord_str in coordinates_str]

def get_vbo_id_of_address(address, cursor):
	print(f'Getting vbo_id for address {address}...')
	query = '''
	SELECT vbo_id
	FROM bag
	WHERE adres=%s
	'''
	cursor.execute(query, (address,))
	results = cursor.fetchall()
	if len(results) == 1:
		vbo_id = results[0][0]
		print(f'Found vbo_id: {vbo_id}')
		return vbo_id
	else:
		return None

def main():

	connection = get_connection()
	cursor = connection.cursor(cursor_factory=DictCursor)

	if '--vbo_id' in sys.argv:
		index = sys.argv.index('--vbo_id')
		vbo_id = sys.argv[index + 1]
	elif '--address' in sys.argv:
		index = sys.argv.index('--address')
		address = sys.argv[index + 1]
		vbo_id = get_vbo_id_of_address(address, cursor)
		if vbo_id == None:
			print('No vbo_id found for the address, please check your address again. It should be of the form "1234AB_123".')
			return
	else:
		raise ValueError('You should specify the dwelling using either the --vbo_id or the --address flag.')

	pipeline('--vbo_id', vbo_id)
	print('\n============\n')

	dwelling = get_bag_vbo(vbo_id, cursor)

	buurt_id = dwelling['buurt_id']
	x, y = parse_geometry(dwelling['geometry'])
	lon, lat = rijksdriehoek_to_wsg84(x, y)

	m = initiate_folium_map(lon, lat)
	results_cursor = get_buurt_results(buurt_id, cursor)
	add_markers_to_map(vbo_id, m, results_cursor)

	fullscreen = Fullscreen()
	fullscreen.add_to(m)

	print('Saving map...')
	current_dir = os.path.dirname(os.path.realpath(__file__))
	filename = f"map-{dwelling['adres']}.html"
	path = os.path.join(current_dir, filename)
	m.save(path)

if __name__ == '__main__':
	main()
