from Map import *
from Utils import DistancePointLine, lineMagnitude
import psycopg2
import time
import math

class TrajPoint(object):
	def __init__(self, timestamp, lon, lat):
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

	def point_matching(self, traj_point, prev_traj_point, prev_seg, prev_candidate):
		print "MapMatching at Time:", time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(traj_point.timestamp))

		candidate = obtain_candidate(traj_point)

		print "Number of Candidates:" , len(candidate)		

		road_id, seg_id = obtain_matching_segment(traj_point, prev_traj_point, prev_seg, candidate)

		#modify backwards
		cur_seg = (road_id, seg_id)
		prev_road_id, prev_seg_id = obtain_matching_segment(prev_traj_point, traj_point, cur_seg, prev_candidate)
		
		return road_id, seg_id, prev_road_id, prev_seg_id

	def obtain_candidate(self, traj_point):
		traj_point.row, traj_point.col = self.traj_map.lon_lat_to_grid_row_col(traj_point.lon, traj_point.lat)
		
		row_l = max(0, traj_point.row - 1)
		row_h = min(self.traj_map.TOTAL_GRID_ROWS - 1, traj_point.row + 1)
		col_l = max(0, traj_point.col - 1)
		col_h = min(self.traj_map.TOTAL_GRID_COLS - 1, traj_point.col + 1)

		search_set = []
		for i in range(row_l, row_h + 1):
			for j in range(col_l, col_h + 1):
				search_set += self.traj_map.grid_road_index[i][j]

		px, py = self.to_standard_xy(traj_point.lon, traj_point.lat)

		candidate = []
		
		for (r,s) in search_set:
			x1, y1 = self.to_standard_xy(self.traj_map.roads[r][s][0], self.traj_map.roads[r][s][1])
			x2, y2 = self.to_standard_xy(self.traj_map.roads[r][s+1][0]. self.traj_map.roads[r][s+1][1])
			dist, lx, ly = DistancePointLine(px, py, x1, y1, x2, y2)
			if dist < maxdist:
				flag = False
				for idx in range(0, len(candidate)):
					if(dist < candidate[idx][0]):
						candidate.insert(idx, (dist, i, j))
						flag = True
						break
				if flag == False:
					candidate.append((dist, i, j))

		return candidate

	def obtain_matching_segment(self, traj_point, prev_traj_point, prev_seg, candidate):
		f_tp = []
		max_result = (0.0, -1, -1)
		for (d, r, s) in candidate:
			op = self.ObservationProbability(d)
			tp = self.TopologicalProbability(r, s, traj_point, prev_traj_point, prev_seg)
			result = op*tp
			f_tp.append((result, op, tp))
			if result > max_result:
				max_result = (result, r, s)
		
		return max_result[1:]
	
	def ObservationProbability(self, d):
		MV = 0 #mean value
		SD = 20 #standard deviation

		op = (1 / math.sqrt(2 * math.pi * SD)) * math.exp(- math.pow(d - MV, 2) / (2 * math.pow(SD, 2)))

		return op

	def TopologicalProbability(self, r, s, traj_point, prev_traj_point, prev_seg):
		prev_x, prev_y = to_standard_xy(prev_traj_point.lon, prev_traj_point.lat)
		prev_seg_x1, prev_seg_y1 = to_standard_xy(self.traj_map.roads[prev_seg[0]][prev_seg[1]][0], self.traj_map.roads[prev_seg[0]][prev_seg[1]][1])
		prev_seg_x2, prev_seg_y2 = to_standard_xy(self.traj_map.roads[prev_seg[0]][prev_seg[1]+1][0], self.traj_map.roads[prev_seg[0]][prev_seg[1]+1][1])
		cur_x, cur_y = to_standard_xy(traj_point.lon, traj_point.lat)
		cur_seg_x1, cur_seg_y1 = to_standard_xy(self.traj_map.roads[r][s][0], self.traj_map.roads[r][s][1])
		cur_seg_x2, cur_seg_y2 = to_standard_xy(self.traj_map.roads[r][s+1][0], self.traj_map.roads[r][s+1][1])
		d1, prev_ix, prev_iy = DistancePointLine(prev_x, prev_y, prev_seg_x1, prev_seg_y1, prev_seg_x2, prev_seg_y2)
		d2, cur_ix, cur_iy = DistancePointLine(cur_x, cur_y, cur_seg_x1, cur_seg_y1, cur_seg_x2, cur_seg_y2)
		
		if (r,s) == prev_seg: #if on the same segment
			w = lineMagnitude(prev_ix, prev_iy, cur_ix, cur_iy)

		else:
			tar_prev[0], tar_prev[1], w0 = self.obtain_shortest_path(prev_seg[0], prev_seg[1], r, s)
			prev_intersection_x, prev_intersection_y = to_standard_xy(self.find_intersection(tar_prev[0], tar_prev[1], r, s))
			
			tar = (r, s)
			while prev_seg != tar_prev:
				tar = tar_prev
				tar_prev[0], tar_prev[1], d = self.obtain_shortest_path(prev_seg[0], prev_seg[1], r, s)

		 	latter_intersection_x, latter_intersection_y = to_standard_xy(self.find_intersection(tar[0], tar[1], prev_seg[0], prev_seg[1]))

			w = w0 + lineMagnitude(prev_ix, prev_iy, latter_intersection_x, latter_intersection_y) + lineMagnitude(prev_intersection_x, prev_intersection_y, cur_ix, cur_iy) #obtain the length of shortest path

		avg_spd = (prev_traj_point.spd + traj_point.spd) / 2
		t = (traj_point.timestamp - prev_traj_point.timestamp) / 60.0 / 60.0
		dist = avg_spd * t #the actual distance of vehicle moving

		if dist < w:
			dist = 2 * w - dist

		tp = 1 - abs(w - dist) / dist

		

	def to_standard_xy(self, lon, lat): #convert longitude, latitude to x,y in meters in the map
		x = (lon - self.traj_map.min_longitude) * self.WIDTH / (self.traj_map.max_longitude - self.traj_map.min_longitude)
		y = self.HEIGHT - (lat - self.traj_map.min_latitude) * self.HEIGHT/ (self.traj_map.max_latitude - self.traj_map.min_latitude)
		
		return x, y
