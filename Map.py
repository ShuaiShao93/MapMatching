import glob
import math
import shapefile
import time
import psycopg2
from Utils import map_dist, line_segment_cross

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
		for row in range(0, self.TOTAL_GRID_ROWS):   #index is one less than actual number of ROWS or COLS
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
				print "gen_road_graph: row = %d, col = %d" % (row+1, col+1)

		print "Number of intersections: ", len(self.intersections)

	def ShortestPath(self):
		print "Connecting to database 'shortest_path'......"
		conn_to = psycopg2.connect(host='localhost', port='5432', database='mapmatching', user='postgres', password='123456')
		print "Connected."
		cursor_to = conn_to.cursor()

		cursor_to.execute("TRUNCATE TABLE shortest_path")
		conn_to.commit()

		self.num_sp = 0

		for i in range(0, len(self.roads)):
			for j in range(0, len(self.roads[i]) - 1):
				#print "Processing the ShortestPath from %d-%d" % (i, j)
				self.Dijkstra(i, j, self.roads, self.road_intersections, cursor_to)

		conn_to.commit()
		conn_to.close()

	def Dijkstra(self, road_id, segment_id, roads, road_intersections, cursor_to):
		INF = 999999

		S = []
		U = []

		row1, col1 = self.lon_lat_to_grid_row_col(roads[road_id][segment_id][0], roads[road_id][segment_id][1])
		row2, col2 = self.lon_lat_to_grid_row_col(roads[road_id][segment_id+1][0], roads[road_id][segment_id+1][1])
		row_l = max(0, min(row1, row2) - 1)
		row_h = min(self.TOTAL_GRID_ROWS - 1, max(row1, row2) + 1)  #index is one less than actual number, so the max index is TOTAL_GRID_ROWS -1
		col_l = max(0, min(col1, col2) - 1)
		col_h = min(self.TOTAL_GRID_COLS - 1, max(col1, col2) + 1)

		search_range = []
		for i in range(row_l, row_h + 1):
			for j in range(col_l, col_h + 1):
				search_range += self.grid_road_index[i][j]
		search_range = set(search_range) # remove the duplicated elements

		SegmentDistance = {}

		for r in search_range:
			SegmentDistance[r] = [INF, -1, -1] #First is distance from this segment, Second and Third are road_id and seg_id of the previous segment in shortest path
			U.append(r)

		SegmentDistance[(road_id, segment_id)] = [0, road_id, segment_id]

		while len(U) != 0:
			minimum = INF
			for seg in U:
				if SegmentDistance[seg][0] < minimum:
					minimum = SegmentDistance[seg][0]
					minidx = seg

			if minimum == INF:
				break

			S.append(minidx)
			U.remove(minidx)

			lon1 = roads[minidx[0]][minidx[1]][0]
			lat1 = roads[minidx[0]][minidx[1]][1]
			lon2 = roads[minidx[0]][minidx[1] + 1][0]
			lat2 = roads[minidx[0]][minidx[1] + 1][1]
			length = map_dist(lon1, lat1, lon2, lat2)

			if minidx[0] in road_intersections:     #renew all intersected segments
				for ist in road_intersections[minidx[0]]:
					if ist[2] == minidx[1]:
						neighbor = ist[3]
					else:
						continue
				
					if not SegmentDistance.has_key(neighbor):
						continue

					if minimum + length < SegmentDistance[neighbor][0]:
						SegmentDistance[neighbor][0] = minimum + length
						SegmentDistance[neighbor][1:] = minidx

			if minidx[1] > 0 and SegmentDistance.has_key((minidx[0], minidx[1] - 1)): #renew adjacent segment in the same road
				if minimum + length < SegmentDistance[(minidx[0], minidx[1] - 1)][0]:
					SegmentDistance[(minidx[0], minidx[1] - 1)][0] = minimum + length
					SegmentDistance[(minidx[0], minidx[1] - 1)][1:] = minidx
			
			if minidx[1] < len(roads[minidx[0]]) - 2 and SegmentDistance.has_key((minidx[0], minidx[1] + 1)): #renew adjacent segment in the same road
				if minimum + length < SegmentDistance[(minidx[0], minidx[1] + 1)][0]:
					SegmentDistance[(minidx[0], minidx[1] + 1)][0] = minimum + length
					SegmentDistance[(minidx[0], minidx[1] + 1)][1:] = minidx

		l0 = map_dist(roads[road_id][segment_id][0], roads[road_id][segment_id][1], roads[road_id][segment_id+1][0], roads[road_id][segment_id+1][1])

		for seg in S:
			if SegmentDistance[seg][0] <=INF and SegmentDistance[seg][0] > 0:
				distance = max(0, SegmentDistance[seg][0] - l0)
				sql = "INSERT INTO shortest_path(src_roadid,src_segmentid,dst_roadid,dst_segmentid,prev_roadid,prev_segmentid,dist) values(%d,%d,%d,%d,%d,%d,%f)" % (road_id, segment_id, seg[0], seg[1], SegmentDistance[seg][1], SegmentDistance[seg][2], distance)
				cursor_to.execute(sql)
				self.num_sp += 1
				print "Shortest Path %8d from %4d/%4d-%3d to %4d-%3d prev: %4d-%3d dist:%8.3f" % (self.num_sp, road_id, len(roads)-1, segment_id, seg[0], seg[1], SegmentDistance[seg][1], SegmentDistance[seg][2], distance)
		
						

if __name__ == '__main__':
	bjmap = Map()
	filenames = ["bjmap_new/road"]
	bjmap.load_roads(filenames)
	bjmap.stat_map_info()

	#bjmap.index_roads_on_grid()
	#bjmap.gen_road_graph()	

	#bjmap.ShortestPath()
