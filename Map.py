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

if __name__ == '__main__':
	bjmap = Map()
	filenames = ["bjmap_new/road"]
	bjmap.load_roads(filenames)
	bjmap.stat_map_info()
