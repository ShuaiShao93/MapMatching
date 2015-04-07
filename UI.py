from Tkinter import *
from Map import *
from Utils import map_dist, rand_color, line_segment_cross, DistancePointLine, is_line_segment_intersects_box, hsv2rgb
import random

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

		self.CANVAS_MIN_X, self.CANVAS_MIN_Y = self.to_canvas_xy(traj_map.min_longitude, traj_map.max_latitude)
		self.CANVAS_MAX_X, self.CANVAS_MAX_Y = self.to_canvas_xy(traj_map.max_longitude, traj_map.min_latitude)

		self.GRID_INTERVAL = 500 * self.RESOLUTION

		self.TOTAL_GRID_ROWS = int((self.CANVAS_MAX_Y - self.CANVAS_MIN_Y) / self.GRID_INTERVAL + 1)
		self.TOTAL_GRID_COLS = int((self.CANVAS_MAX_X - self.CANVAS_MIN_X) / self.GRID_INTERVAL + 1)

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

	def to_canvas_xy(self, lon, lat):
		x = (lon - self.traj_map.min_longitude) * (self.CANVAS_WIDTH * self.scale) / (self.traj_map.max_longitude - self.traj_map.min_longitude)
		y = self.CANVAS_HEIGHT * self.scale - (lat - self.traj_map.min_latitude) * (self.CANVAS_HEIGHT * self.scale)/ (self.traj_map.max_latitude - self.traj_map.min_latitude)
		
		return x, y

	def to_lon_lat(self, x, y):
		lon = x * (self.traj_map.max_longitude - self.traj_map.min_longitude) / (self.CANVAS_WIDTH * self.scale) + self.traj_map.min_longitude
		lat = (self.CANVAS_HEIGHT * self.scale - y) * (self.traj_map.max_latitude - self.traj_map.min_latitude) / (self.CANVAS_HEIGHT * self.scale) + self.traj_map.min_latitude

		return lon, lat

	def draw_map(self):
		for i in range(0, len(self.traj_map.roads)):
			p = map(lambda x: self.to_canvas_xy(x[0], x[1]), self.traj_map.roads[i])
			if len(p) >= 2:
				self.canv.create_line(p, fill = "grey", tag = "map", width = 1)
		self.canv.itemconfig("map", state = self.CHECK_BUTTON_STATES[self.var_cb_map.get()])
		self.canv.config(scrollregion = self.canv.bbox(ALL))

	def onCanvasMotion(self, event): #show the position of mouse on map
		lon, lat = self.to_lon_lat(self.canv.canvasx(event.x), self.canv.canvasy(event.y))
		self.var_pos.set("(%4.4f, %4.4f), scale=%.2f" % (lon, lat, self.scale))

	def onCanvasLeftDoubleClick(self, event):
		self.zoomIn(event.x, event.y)
		self.onCanvasMotion(event)  #refresh the footer

	def onCanvasRightDoubleClick(self, event):
		self.zoomOut(event.x, event.y)
		self.onCanvasMotion(event) #refresh the footer

	def zoomIn(self, x, y, scale = 1.2):
		self.scale *= scale
		cx, cy = self.canv.canvasx(x), self.canv.canvasy(y)
		self.canv.scale(ALL, cx, cy, scale, scale)
		self.canv.config(scrollregion = self.canv.bbox(ALL))

	def zoomOut(self, x, y, scale = 1.2):
		self.scale /= scale
		cx, cy = self.canv.canvasx(x), self.canv.canvasy(y)
		self.canv.scale(ALL, cx, cy, 1.0/scale, 1.0/scale)
		self.canv.config(scrollregion = self.canv.bbox(ALL))

if __name__ == "__main__":
	bjmap = Map()
	filenames = ["bjmap_new/road"]
	bjmap.load_roads(filenames)
	bjmap.stat_map_info()	

	master = Tk()
	map_canvas = MapCanvas(bjmap, master)
	map_canvas.draw_map()

	mainloop()		
