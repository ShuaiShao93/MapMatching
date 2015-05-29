from Tkinter import *
from Map import *
from Matching import *
import random
import json
import time
from Utils import DistancePointLine

class MapCanvas(Frame):
	CHECK_BUTTON_STATES = ["hidden", "normal"]

	def __init__(self, traj_map, parent = None, resolution = 0.02):  #resolution: pixel/meter	
		self.traj_map = traj_map
		self.RESOLUTION = resolution
		m_latitude = (traj_map.min_latitude + traj_map.max_latitude) / 2
		self.CANVAS_WIDTH = resolution * map_dist(traj_map.min_longitude, m_latitude, traj_map.max_longitude, m_latitude)
		m_longitude = (traj_map.min_longitude + traj_map.max_longitude) / 2
		self.CANVAS_HEIGHT = resolution * map_dist(m_longitude, traj_map.min_latitude, m_longitude, traj_map.max_latitude)

		self.scale = 1.0 #zoomin/zoomout

		self.cx = self.CANVAS_WIDTH/2
		self.cy = self.CANVAS_HEIGHT/2
		self.clon = m_longitude
		self.clat = m_latitude
		#self.CANVAS_MIN_X, self.CANVAS_MIN_Y = self.to_canvas_xy(traj_map.min_longitude, traj_map.max_latitude)
		#self.CANVAS_MAX_X, self.CANVAS_MAX_Y = self.to_canvas_xy(traj_map.max_longitude, traj_map.min_latitude)

		self.radius = 0.1 #radius of the point drawed

		Frame.__init__(self, parent)
		self.pack(expand = YES, fill = BOTH)
		
		f_main = Frame(self)
		f_main.pack(expand = YES, fill = BOTH)

		self.canv = Canvas(f_main)
		self.canv.config(width = 800, height = 600)
		self.canv.config(highlightthickness=0)
		
		self.f_panel = Frame(f_main)
		self.f_panel.pack(side = RIGHT, fill = Y)

		Label(self.f_panel, text = "Map Layers").pack()
		self.var_cb_map = IntVar()
		cb_map = Checkbutton(self.f_panel, text="Map", variable = self.var_cb_map, onvalue = 1, offvalue = 0, height = 5, width = 20, command = lambda:self.onLayerRedraw("map", self.var_cb_map))
		cb_map.select()
		cb_map.pack()	

		self.canv.pack(side = TOP, expand = YES, fill = BOTH)
		self.canv.bind('<Motion>', self.onCanvasMotion)
		self.canv.bind('<Double-Button-1>', self.onCanvasLeftDoubleClick)
		self.canv.bind('<Double-Button-3>', self.onCanvasRightDoubleClick)

		self.bar_x = Scrollbar(f_main, orient = HORIZONTAL)
		self.bar_x.config(command = self.canv.xview)
		self.canv.config(xscrollcommand = self.bar_x.set)
		self.bar_x.pack(side = BOTTOM, fill = X, before = self.canv)

		self.bar_y = Scrollbar(f_main)
		self.bar_y.config(command = self.canv.yview)
		self.canv.config(yscrollcommand = self.bar_y.set)
		self.bar_y.pack(side = RIGHT, fill = Y, before = self.canv)

		self.var_pos = StringVar()
		self.footer = Label(self, textvariable = self.var_pos)
		self.footer.pack(fill = BOTH)

		self.traj_var_cb = {}
		self.traj_mm_var_cb = {}
	
	#the principle of zoom in/out is not to change the x,y of the point where you double clicked and the point is self.cx,cy
	def to_canvas_xy(self, lon, lat):
		x = self.cx + (lon - self.clon) * (self.CANVAS_WIDTH * self.scale) / (self.traj_map.max_longitude - self.traj_map.min_longitude)
		y = self.cy - (lat - self.clat) * (self.CANVAS_HEIGHT * self.scale) / (self.traj_map.max_latitude - self. traj_map.min_latitude)
		
		return x, y

	def to_canvas_xy_t(self, lon, lat):
		x = (lon - self.traj_map.min_longitude) * (self.CANVAS_WIDTH) / (self.traj_map.max_longitude - self.traj_map.min_longitude)
		y = self.CANVAS_HEIGHT - (lat - self.traj_map.min_latitude) * (self.CANVAS_HEIGHT)/ (self.traj_map.max_latitude - self.traj_map.min_latitude)
		
		return x, y

	def to_lon_lat(self, x, y):
		lon = self.clon + (x - self.cx) * (self.traj_map.max_longitude - self.traj_map.min_longitude) / (self.CANVAS_WIDTH * self.scale)
		lat = self.clat - (y - self.cy) * (self.traj_map.max_latitude - self.traj_map.min_latitude) / (self.CANVAS_HEIGHT * self.scale)

		return lon, lat

	def draw_map(self):
		for i in range(0, len(self.traj_map.roads)):
			p = map(lambda x: self.to_canvas_xy(x[0], x[1]), self.traj_map.roads[i])
			if len(p) >= 2:
				self.canv.create_line(p, fill = "grey", tag = "map", width = 1)
		self.canv.itemconfig("map", state = self.CHECK_BUTTON_STATES[self.var_cb_map.get()])
		self.canv.config(scrollregion = self.canv.bbox(ALL))

	def load_traj(self, f):
		print "Loading traj_file!"
		self.traj = {}
		for filename in f:
			self.traj[filename] = []
			print filename
			self.traj_file = open(filename, 'r')
			while True:
				lines = self.traj_file.readlines(100000)
				if not lines:
					break
				for line in lines:
					self.traj[filename].append(json.loads(line))

			print "Succeed to load traj", filename

		self.var_cb_traj = IntVar()
		cb_traj = Checkbutton(self.f_panel, text = "trajectory", variable = self.var_cb_traj, onvalue = 1, offvalue = 0, height = 5, width = 20, command = lambda: self.onLayerRedraw("traj", self.var_cb_traj))
		cb_traj.select()
		cb_traj.pack()

		self.var_cb_mm = IntVar()
		cb_mm = Checkbutton(self.f_panel, text = "matching_traj", variable = self.var_cb_mm, onvalue = 1, offvalue = 0, height = 5, width = 20, command = lambda: self.onLayerRedraw("matching_traj", self.var_cb_mm))
		cb_mm.select()
		cb_mm.pack()

	def get_point(self, i, filename):
		p = TrajPoint(self.traj[filename][i]["devicesn"],self.traj[filename][i]["timestamp"], self.traj[filename][i]["longitude"], self.traj[filename][i]["latitude"], self.traj[filename][i]["speed"])
		
		return p 

	def draw_traj(self, traj_point, search_range = 20):
		x, y = self.to_canvas_xy(traj_point.lon, traj_point.lat)
		self.canv.create_oval(x-self.radius, y-self.radius, x+self.radius, y+self.radius, fill = "red", tag = "traj", state = self.CHECK_BUTTON_STATES[self.var_cb_traj.get()])
		#self.canv.cerate_line()
		r = search_range * self.RESOLUTION * self.scale
		#self.canv.create_oval(x-r, y-r, x+r, y+r, tag = "traj", state = self.CHECK_BUTTON_STATES[self.var_cb_traj.get()])
		
	def draw_matching_traj(self, point, roadid, segid):
		if (roadid, segid) == (-1, -1):
			return -1
		lon1, lat1 = self.traj_map.roads[roadid][segid]
		lon2, lat2 = self.traj_map.roads[roadid][segid+1]
		lon, lat = point.lon, point.lat
		x1, y1 = self.to_canvas_xy(lon1, lat1)
		x2, y2 = self.to_canvas_xy(lon2, lat2)
		x, y = self.to_canvas_xy(lon, lat)
		d, ix, iy = DistancePointLine(x, y, x1, y1, x2, y2)
		self.canv.create_oval(ix-self.radius, iy-self.radius, ix+self.radius, iy+self.radius, fill = "yellow", tag = "matching_traj", state = self.CHECK_BUTTON_STATES[self.var_cb_mm.get()])

	def replace_matching_traj(self, point, seg):
		if seg == (-1, -1):
			return -1

		lon1, lat1 = self.traj_map.roads[seg[0]][seg[1]]
		lon2, lat2 = self.traj_map.roads[seg[0]][seg[1]+1]
		lon, lat = point.lon, point.lat
		x1, y1 = self.to_canvas_xy(lon1, lat1)
		x2, y2 = self.to_canvas_xy(lon2, lat2)
		x, y = self.to_canvas_xy(lon, lat)
		d, ix, iy = DistancePointLine(x, y, x1, y1, x2, y2)
		self.canv.create_oval(ix-self.radius, iy-self.radius, ix+self.radius, iy+self.radius, fill = "blue", tag = "matching_traj", state = self.CHECK_BUTTON_STATES[self.var_cb_mm.get()])	

	def onCanvasMotion(self, event): #show the position of mouse on map
		lon, lat = self.to_lon_lat(self.canv.canvasx(event.x), self.canv.canvasy(event.y))
		self.var_pos.set("(%4.4f, %4.4f), scale=%.2f" % (lon, lat, self.scale))

	def onCanvasLeftDoubleClick(self, event):
		self.zoomIn(event.x, event.y)
		self.onCanvasMotion(event)  #refresh the footer

	def onCanvasRightDoubleClick(self, event):
		self.zoomOut(event.x, event.y)
		self.onCanvasMotion(event) #refresh the footer

	def zoomIn(self, x, y, scale = 1.4):
		cx, cy = self.canv.canvasx(x), self.canv.canvasy(y)
		self.clon, self.clat = self.to_lon_lat(cx, cy)
		self.cx, self.cy = cx, cy
		self.scale *= scale
		self.radius *= scale
		self.canv.scale(ALL, self.cx, self.cy, scale, scale)
		self.canv.config(scrollregion = self.canv.bbox(ALL))

	def zoomOut(self, x, y, scale = 1.4):
		cx, cy = self.canv.canvasx(x), self.canv.canvasy(y)
		self.clon, self.clat = self.to_lon_lat(cx, cy)
		self.cx, self.cy = cx, cy
		self.scale /= scale
		self.radius /= scale
		self.canv.scale(ALL, self.cx, self.cy, 1.0/scale, 1.0/scale)
		self.canv.config(scrollregion = self.canv.bbox(ALL))

	def onLayerRedraw(self, tag, var):
		self.canv.itemconfig(tag, state=MapCanvas.CHECK_BUTTON_STATES[var.get()])

	def highlight_intersections(self):
		for ist in self.traj_map.intersections:
			cix, ciy = self.to_canvas_xy(ist[0], ist[1])
			self.canv.create_oval(cix - 0.01, ciy - 0.01, cix + 0.01, ciy + 0.01, fill = "yellow")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def wg_to_Mars(self, wgLon, wgLat):
		a = 6378245.0
		ee = 0.00669342162296594323

		dLat = self.transformLat(wgLon - 105.0, wgLat - 35.0)
		dLon = self.transformLon(wgLon - 105.0, wgLat - 35.0)
		radLat = wgLat / 180.0 * math.pi
		magic = math.sin(radLat)
		magic = 1 - ee * magic * magic
		sqrtMagic = math.sqrt(magic)
		dLat = (dLat * 180.0) / ((a * (1.0 - ee)) / (magic * sqrtMagic) * math.pi)
		dLon = (dLon * 180.0) / (a / sqrtMagic * math.cos(radLat) * math.pi)
		mgLat = wgLat + dLat
		mgLon = wgLon + dLon

		return mgLon, mgLat

	def transformLat(self, x, y):
		ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
		ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
		ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
		ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
		return ret

	def transformLon(self, x, y):
		ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
		ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
		ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
		ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
		return ret
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def Mars_to_bd(self, mg_lon, mg_lat):
		pi = math.pi
		x_pi = math.pi * 3000.0 / 180.0

		x = mg_lon
		y = mg_lat  
		z = math. sqrt(x * x + y * y) + 0.00002 * math.sin(y * x_pi)
		theta = math.atan2(y, x) + 0.000003 * math.cos(x * x_pi)
		bd_lon = z * math.cos(theta) + 0.0065
		bd_lat = z * math.sin(theta) + 0.006

		return bd_lon, bd_lat

	def bd_to_Mars(self, bd_lon, bd_lat):
		pi = math.pi
		x_pi = math.pi * 3000.0 / 180.0

		x = bd_lon - 0.0065
		y = bd_lat - 0.006
		z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
		theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
		mg_lon = z * math.cos(theta)
		mg_lat = z * math.sin(theta)

		return mg_lon, mg_lat
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def wg_to_bd(self, wg_lon, wg_lat):
		mg_lon, mg_lat = self.wg_to_Mars(wg_lon, wg_lat)
		bd_lon, bd_lat = self.Mars_to_bd(mg_lon, mg_lat)

		return bd_lon,bd_lat
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == "__main__":
	bjmap = Map()
	filenames = ["bjmap_new/road"]
	bjmap.load_roads(filenames)
	bjmap.stat_map_info()	

	bjmap.index_roads_on_grid()
	bjmap.gen_road_graph()

	matching_module = Matching(bjmap, 100)

	master = Tk()
	map_canvas = MapCanvas(bjmap, master)
	map_canvas.draw_map()

	traj_file = []
	traj_file.append("oneMonthData/oneMonth_967790112791.txt")
	map_canvas.load_traj(traj_file)
	time_sum  = 0.0 # record the time consumption for matching


	for f in traj_file:
		prev_point = -1
		prev_seg = (-1, -1)
		for i in range(0, len(map_canvas.traj[f])):
			print "Matching No.", i + 1
			point = map_canvas.get_point(i, f)
			#point.lon, point.lat =  map_canvas.wg_to_Mars(point.lon, point.lat)
			map_canvas.draw_traj(point)
	
			master.update()

			t1 = time.time()
			road_id, seg_id, prev_road_id, prev_seg_id = matching_module.point_matching(point)
			t2 = time.time()
			t = t2 - t1
			#print "No. %d Matching spends %f seconds" % (i + 1, t)
			time_sum += t
			print "The average time for mapmatching is", time_sum / (i + 1.0)	

			map_canvas.draw_matching_traj(point, road_id, seg_id)

			if (prev_road_id, prev_seg_id) != (-1, -1):
				map_canvas.replace_matching_traj(prev_point, prev_seg)
				map_canvas.draw_matching_traj(prev_point, prev_road_id, prev_seg_id)	

			prev_point = point
			prev_seg = (road_id, seg_id)
	
			master.update()


	#map_canvas.highlight_intersections()

	mainloop()		
