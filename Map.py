import glob
import math
import shapefile
import sys
import time
import psycopg2
from Utils import map_dist, is_line_segment_intersects_box, line_segment_cross

#class TrajectoryPoint(object, timestamp, lon, lat):
#	self.timestamp, self.lon, self.lat = timestamp, lon, lat
#	self.row = self.col = -1

class Map(object):
	def __init__(self, grid_interval=300):
		self.GRID_INTERVAL = grid_interval

		self.roads = []
		self.road_names= []
		self.grid_road_index = []
		self.intersections = []
		self.road_intersections = {}

	
	def load_roads(self, filenames):
		shapeRecords = reduce(lambda r1,r2: x+y, map(lambda f: shapefile.Reader(f).shapeRecords(), filenames))
		self.roads += filter(lambda n: len(n)>2, map(lambda r: r.shape.points, shapeRecords))
		self.road_names += map(lambda r: r.record[0], shapeRecords)
		min_lon = min(map(lambda r: min(map(lambda p: p[0], r)), self.roads))		
		max_lon = max(map(lambda r: max(map(lambda p: p[0], r)), self.roads))
		min_lat = min(map(lambda r: min(map(lambda p: p[1], r)), self.roads))
		max_lat = max(map(lambda r: max(map(lambda p: p[1], r)), self.roads))
		self.min_longitude = min_lon
		self.max_longitude = max_lon
		self.min_latitude = min_lat
		self.max_latitude = max_lat

		m_longitude = (self.min_longitude + self.max_longitude)/2
		m_latitude = (self.min_latitude + self.max_latitude)/2
		self.UNIT_LONGITUDE_DISTANCE = map_dist(self.min_longitude, m_latitude, self.max_longitude, m_latitude) / (self.max_longitude - self.min_longitude)
		self.UNIT_LATITUDE_DISTANCE = map_dist(m_longitude, self.min_latitude, m_longitude, self.max_latitude) / (self.max_latitude - self.min_latitude)
		self.GRID_INTERVAL_LONGITUDE = self.GRID_INTERVAL / self.UNIT_LONGITUDE_DISTANCE
		self.GRID_INTERVAL_LATITUDE = self.GRID_INTERVAL / self.UNIT_LATITUDE_DISTANCE
		self.TOTAL_GRID_ROWS = int((self.max_latitude - self.min_latitude) / self.GRID_INTERVAL_LATITUDE) + 1
		self.TOTAL_GRID_COLS = int((self.max_longitude - self.min_longitude) / self.GRID_INTERVAL_LONGITUDE) + 1

	def stat_map_info(self):
		roads_number = len(self.roads)
		points_number = reduce(lambda r1, r2: r1 + r2, map(lambda r: len(r), self.roads))
		print "Total number of roads: %d" % roads_number
		print "Total number of points: %d" % points_number
		print "Total number of road segments: %d" % (points_number - roads_number)
		
		print "min_longitude:", self.min_longitude
		print "max_longitude:", self.max_longitude
		print "min_latitude:", self.min_latitude
		print "max_latitude:", self.max_latitude

	def lon_lat_to_grid_row_col(self, lon, lat):
		row = int((self.max_latitude - lat) / self.GRID_INTERVAL_LATITUDE)
		col = int((lon - self.min_longitude) / self.GRID_INTERVAL_LONGITUDE)
		return row, col

	def index_roads_on_grid(self):
		self.grid_road_index = []
		for row in range(0, self.TOTAL_GRID_ROWS):
			self.grid_road_index.append([])
			for col in range(0, self.TOTAL_GRID_COLS):
				self.grid_road_index[row].append([])
		for i in range(0, len(self.roads)):
			for j in range(0, len(self.roads[i]) - 1):
				lon1, lat1 = self.roads[i][j][0], self.roads[i][j][1]
				lon2, lat2 = self.roads[i][j+1][0], self.roads[i][j+1][1]
				row1, col1 = self.lon_lat_to_grid_row_col(lon1,lat1)
				row2, col2 = self.lon_lat_to_grid_row_col(lon2,lat2)
				
				for row in range(min(row1,row2), max(row1, row2) + 1):
					for col in range(min(col1, col2), max(col1, col2) + 1):
						self.grid_road_index[row][col].append((i, j))

	#deal with the intersections in one grid cell
	def gen_intersections_in_grid_cell(self, row, col):
		segments = self.grid_road_index[row][col]
		for i in range(0, len(segments) - 1):
			for j in range(i + 1, len(segments)):
				road_id1, seg_id1 = segments[i]
				road_id2, seg_id2 = segments[j]
				if road_id1 == road_id2:
					continue
				x0, y0 = self.roads[road_id1][seg_id1]	
				x1, y1 = self.roads[road_id1][seg_id1+1]
				x2, y2 = self.roads[road_id2][seg_id2]
				x3, y3 = self.roads[road_id2][seg_id2+1]
				ix, iy = line_segment_cross(x0, y0, x1, y1, x2, y2, x3, y3)

				if ix and iy:
					if road_id1 not in self.road_intersections:
						self.road_intersections[road_id1] = set()
					if road_id2 not in self.road_intersections:
						self.road_intersections[road_id2] = set()
				
					k = (ix, iy, (road_id1, seg_id1), (road_id2, seg_id2))
					self.intersections.append(k)

					self.road_intersections[road_id1].add((ix, iy, seg_id1, (road_id2, seg_id2)))
					self.road_intersections[road_id2].add((ix, iy, seg_id2, (road_id1, seg_id1)))

	#handle all intersections
	def gen_road_graph(self):
		for row in range(0, self.TOTAL_GRID_ROWS):
			for col in range(0, self.TOTAL_GRID_COLS):
				self.gen_intersections_in_grid_cell(row, col)
				print "gen_road_graph: row = %d, col = %d" % (row, col)

		print "Number of intersections: ", len(self.intersections)

						

if __name__ == '__main__':
	bjmap = Map()
	filenames = ["bjmap_new/road"]
	bjmap.load_roads(filenames)
	bjmap.stat_map_info()

	bjmap.index_roads_on_grid()
	bjmap.gen_road_graph()	
