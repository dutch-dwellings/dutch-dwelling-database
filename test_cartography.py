import folium
from folium.plugins import BeautifyIcon

from pyproj import Proj, transform

from psycopg2.extras import DictCursor

from utils.database_utils import get_connection

VBO_ID = '0363010001957132'
BUURT_ID = 'BU03638703'

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

def get_results(cursor):

	query = '''
	SELECT vbo_id, geometry, oppervlakte, adres
	FROM bag
	WHERE buurt_id = %s
	ORDER BY
	RANDOM()
	LIMIT 10
	'''

	# query = '''
	# SELECT *
	# FROM bag, results
	# WHERE
	# bag.vbo_id = results.vbo_id
	# AND results.vbo_id='0363010012156802'
	# '''

	print('Executing query...')
	cursor.execute(query, (BUURT_ID,))
	return cursor

def add_results_to_map(m, cursor):

	print('Iterating through results...')
	i = 0

	for row in cursor:
		dwelling = dict(row)

		icon = BeautifyIcon(
			icon_shape='circle-dot',
			border_color='red',
			border_width=3,
		)

		i += 1
		x, y = parse_geometry(dwelling['geometry'])
		lon, lat = rijksdriehoek_to_wsg84(x, y)
		folium.Marker((lon, lat),icon=icon).add_to(m)

		print(f'\tprocessing: {i} ({dwelling["adres"]})', end='\r')
	print('')

def parse_multipolygon(multipolygon):
	coordinates_str = multipolygon.replace("MULTIPOLYGON (((", "").replace(")))", "").split(', ')

	def parse_coordinate(coordinate_str):
		x_str, y_str = coordinate_str.split(" ")
		x, y = float(x_str), float(y_str)
		lat, lon = rijksdriehoek_to_wsg84(x, y)
		# GeoJSON uses reverse ordering, confusingly...
		return [lon, lat]

	return [parse_coordinate(coord_str) for coord_str in coordinates_str]

def initiate_folium_map():
	print('Creating map...')
	return folium.Map(location=(52.34782062300883, 4.8370537819091695), tiles='cartodb positron', zoom_start=16)

def get_warmtenetten(cursor):
	print('Executing warmtenetten query...')
	query = "SELECT fid, geometrie, percentage_stadsverwarming FROM rvo_warmtenetten WHERE gemeente_naam = 'Amsterdam' LIMIT 10"
	cursor.execute(query)
	print('Fetching results')
	return cursor.fetchall()

def add_warmtenet_to_map(m, warmtenet):
	fid, geometrie, percentage_stadsverwarming = warmtenet
	print(f'Parsing multipolygon for {fid}...')
	polygon = parse_multipolygon(geometrie)

	geo_json_template = '''
	{{
	"type": "FeatureCollection",
	"features": [
		{{
			"type": "Feature",
			"properties": {{}},
			"geometry": {{
				"type": "Polygon", 
				"coordinates": [
					{}
				]
			}}
		}}
	]
	}}'''

	geo_json_data = geo_json_template.format(polygon)
	print(f'Adding {fid} to the map...')
	folium.GeoJson(geo_json_data).add_to(m)

def add_warmtenetten_to_map(m, warmtenetten):
	print('Adding warmtenetten to the map...')
	for warmtenet in warmtenetten:
		add_warmtenet_to_map(m, warmtenet)

def main():

	connection = get_connection()
	cursor = connection.cursor(cursor_factory=DictCursor)

	m = initiate_folium_map()

	cursor = get_results(cursor)
	add_results_to_map(m, cursor)

	print('Saving map...')
	m.save('index.html')

if __name__ == '__main__':
	main()
