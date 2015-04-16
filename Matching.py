from Map import *
from Utils import DistancePointLine, lineMagnitude
import psycopg2
import time
import math

class TrajPoint(object):
	def __init__(self, timestamp, lon, lat, spd):
		self.timestamp, self.lon, self.lat, self.spd= timestamp, lon, lat, spd
		self.row = self.col = -1

class Matching(object):
	def __init__ (self, traj_map, search_range = 50):
		self.traj_map = traj_map
		self.search_range = search_range

		#for constructing a coordinate map in meters
		m_latitude = (traj_map.min_latitude + traj_map.max_latitude) / 2
		self.WIDTH = map_dist(traj_map.min_longitude, m_latitude, traj_map.max_longitude, m_latitude)
		m_longitude = (traj_map.min_longitude + traj_map.max_longitude) / 2
		self.HEIGHT = map_dist(m_longitude, traj_map.min_latitude, m_longitude, traj_map.max_latitude)

		print "Connecting..Database: shortest_path..."
		self.conn_sp = psycopg2.connect(host='localhost', port='5432', database="mapmatching", user='postgres',password='123456')

		print "Connected!"
		self.cursor_sp = self.conn_sp.cursor()

	def __del__ (self):
		self.conn_sp.commit()
		self.conn_sp.close()

	def point_matching(self, traj_point, prev_traj_point, prev_seg, prev_candidate):
		print "MapMatching at Time:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(traj_point.timestamp))

		candidate = self.obtain_candidate(traj_point)

		print "Number of Candidates:" , len(candidate)		

		road_id, seg_id = self.obtain_matching_segment(traj_point, prev_traj_point, prev_seg, candidate)
		if (road_id, seg_id) != (-1, -1):
			print "Matching Successfully!"

		#modify backwards
		prev_road_id, prev_seg_id = -1, -1
		if prev_traj_point != -1 and (road_id, seg_id) != (-1, -1): #if it is the first point or there is no matching result for current point, no need to modify backwards
			cur_seg = (road_id, seg_id)
			prev_road_id, prev_seg_id = self.obtain_matching_segment(prev_traj_point, traj_point, cur_seg, prev_candidate)

		if (prev_road_id, prev_seg_id) == (-1, -1):
			return road_id, seg_id, prev_seg[0], prev_seg[1], candidate
		else:	
			return road_id, seg_id, prev_road_id, prev_seg_id, candidate
			print "Modify Backwards Successfully!"

	def obtain_candidate(self, traj_point):
		traj_point.row, traj_point.col = self.traj_map.lon_lat_to_grid_row_col(traj_point.lon, traj_point.lat)
		
		row_l = max(0, traj_point.row - 1)
		row_h = min(self.traj_map.TOTAL_GRID_ROWS - 1, traj_point.row + 1)
		col_l = max(0, traj_point.col - 1)
		col_h = min(self.traj_map.TOTAL_GRID_COLS - 1, traj_point.col + 1)

		search_set = set()
		for i in range(row_l, row_h + 1):
			for j in range(col_l, col_h + 1):
				search_set = search_set | set(self.traj_map.grid_road_index[i][j])

		px, py = self.to_standard_xy(traj_point.lon, traj_point.lat)

		candidate = []
		
		for (r,s) in search_set:
			x1, y1 = self.to_standard_xy(self.traj_map.roads[r][s][0], self.traj_map.roads[r][s][1])
			x2, y2 = self.to_standard_xy(self.traj_map.roads[r][s+1][0], self.traj_map.roads[r][s+1][1])
			dist, lx, ly = DistancePointLine(px, py, x1, y1, x2, y2)
			if dist < self.search_range:
				flag = False
				for idx in range(0, len(candidate)):
					if(dist < candidate[idx][0]):
						candidate.insert(idx, (dist, r, s))
						flag = True
						break
				if flag == False:
					candidate.append((dist, r, s))

		return candidate

	def obtain_matching_segment(self, traj_point, prev_traj_point, prev_seg, candidate):
		f_tp = []
		max_result = (0.0, -1, -1)
		for (d, r, s) in candidate:
			op = self.ObservationProbability(d)
			if prev_traj_point == -1 or prev_seg == (-1,-1): #if it is the first point or previous point has no result, then ignore the topological probability
				tp = 1
			else:
				tp = self.TopologicalProbability(r, s, traj_point, prev_traj_point, prev_seg)
			result = op*tp
			f_tp.append((result, op, tp))
			if result > max_result[0]:
				max_result = (result, r, s)

		if max_result[0] == 0:
			print "Warning!No Matched Segment!"
		
		return max_result[1:]
	
	def ObservationProbability(self, d):
		MV = 0 #mean value
		SD = 20 #standard deviation

		op = (1 / math.sqrt(2 * math.pi * SD)) * math.exp(- math.pow(d - MV, 2) / (2 * math.pow(SD, 2)))

		return op

	def TopologicalProbability(self, r, s, traj_point, prev_traj_point, prev_seg):
		prev_x, prev_y = self.to_standard_xy(prev_traj_point.lon, prev_traj_point.lat)
		prev_seg_x1, prev_seg_y1 = self.to_standard_xy(self.traj_map.roads[prev_seg[0]][prev_seg[1]][0], self.traj_map.roads[prev_seg[0]][prev_seg[1]][1])
		prev_seg_x2, prev_seg_y2 = self.to_standard_xy(self.traj_map.roads[prev_seg[0]][prev_seg[1]+1][0], self.traj_map.roads[prev_seg[0]][prev_seg[1]+1][1])
		cur_x, cur_y = self.to_standard_xy(traj_point.lon, traj_point.lat)
		cur_seg_x1, cur_seg_y1 = self.to_standard_xy(self.traj_map.roads[r][s][0], self.traj_map.roads[r][s][1])
		cur_seg_x2, cur_seg_y2 = self.to_standard_xy(self.traj_map.roads[r][s+1][0], self.traj_map.roads[r][s+1][1])
		d1, prev_ix, prev_iy = DistancePointLine(prev_x, prev_y, prev_seg_x1, prev_seg_y1, prev_seg_x2, prev_seg_y2)
		d2, cur_ix, cur_iy = DistancePointLine(cur_x, cur_y, cur_seg_x1, cur_seg_y1, cur_seg_x2, cur_seg_y2)
		
		if (r,s) == prev_seg: #if on the same segment
			w = lineMagnitude(prev_ix, prev_iy, cur_ix, cur_iy)

		else:
			tar_prev = (-1,-1)
			sp = self.obtain_shortest_path(prev_seg[0], prev_seg[1], r, s)
			tar_prev = sp[0:2]
			w0 = sp[2]
			if w0 == -1: #no shortest_path
				return 0

			intersection = self.find_intersection(tar_prev[0], tar_prev[1], r, s)
			prev_intersection_x, prev_intersection_y = self.to_standard_xy(intersection[0], intersection[1])
			
			tar = (r, s)
			while prev_seg != tar_prev:
				tar = tar_prev
				sp = self.obtain_shortest_path(prev_seg[0], prev_seg[1], r, s)
				tar_prev = sp[0:2]
				d = sp[2]

			intersection = self.find_intersection(tar[0], tar[1], prev_seg[0], prev_seg[1])
		 	latter_intersection_x, latter_intersection_y = self.to_standard_xy(intersection[0], intersection[1])

			w = w0 + lineMagnitude(prev_ix, prev_iy, latter_intersection_x, latter_intersection_y) + lineMagnitude(prev_intersection_x, prev_intersection_y, cur_ix, cur_iy) #obtain the length of shortest path

		avg_spd = (prev_traj_point.spd + traj_point.spd) / 2.0
		t = (traj_point.timestamp - prev_traj_point.timestamp) / 60.0 / 60.0
		dist = avg_spd * t #the actual distance of vehicle moving

		if dist < w:
			dist = 2.0 * w - dist

		tp = 1 - abs(w - dist) / dist

		return tp

	def obtain_shortest_path(self, r1, s1, r2, s2):
		sql = "SELECT prev_roadid, prev_segmentid, dist FROM shortest_path WHERE src_roadid = %d AND src_segmentid = %d AND dst_roadid = %d AND dst_segmentid = %d" % (r1, s1, r2, s2)
		self.cursor_sp.execute(sql)
		result = self.cursor_sp.fetchall()

		if len(result) == 0:
			#print "Failed to obtain shortest path!"
			return -1, -1, -1

		return result[0]
		

	def find_intersection(self, r1, s1, r2, s2):
		if r1 == r2 and abs(s1-s2) == 1:
			return self.traj_map.roads[r1][max(s1, s2)]

		for inters in self.traj_map.road_intersections[r1]:
			if inters[2] == s1 and inters[3] == (r2, s2):
				return inters[:2]

		print "ERROR! Failed to find intersection!!"

		return -1, -1
		

	def to_standard_xy(self, lon, lat): #convert longitude, latitude to x,y in meters in the map
		x = (lon - self.traj_map.min_longitude) * self.WIDTH / (self.traj_map.max_longitude - self.traj_map.min_longitude)
		y = self.HEIGHT - (lat - self.traj_map.min_latitude) * self.HEIGHT/ (self.traj_map.max_latitude - self.traj_map.min_latitude)
		
		return x, y
