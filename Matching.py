from Map import *
import psycopg2
import time

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
		
		for r,s in search_set:
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



	def to_standard_xy(self, lon, lat): #convert longitude, latitude to x,y in meters in the map
		x = (lon - self.traj_map.min_longitude) * self.WIDTH / (self.traj_map.max_longitude - self.traj_map.min_longitude)
		y = self.HEIGHT - (lat - self.traj_map.min_latitude) * self.HEIGHT/ (self.traj_map.max_latitude - self.traj_map.min_latitude)
		
		return x, y
