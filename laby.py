#!/usr/bin/python3

#                north                 ^
#             [                        |  
#             [x x x x x x]            | height  
#      west   [x x x x x x] east       |  
#             [x x x x x x]            |      
#                          ]           v    
#                                      
#             <------------> width 
# 
#								south


import random
import math
import curses
import time
import datetime

east=1
south=2
west=3
north=4

class Cell:
	def __init__(self):
		self.digged=False
		self.marker=None

class Laby:
	def __init__(self):
		self.height=50
		self.width=150
		self.exit=[-1,-1]
		self.map=[[Cell() for i in range(0, self.width)] for j in range(0, self.height)]
		self.light_color=[0,232,233,234,235,52,88,130,172,214,220,226] # 12

	def possible_directions(self, x, y, digging):
# return east, south, west, north 
		dir=[] 
		if x>0:
			if (digging or (self.map[y][x-1].digged)):
				dir.append(west)
		if y>0:
			if (digging or (self.map[y-1][x].digged)):
				dir.append(north)
		if digging:
			dir.append(south)
			dir.append(east)
		else: 
			if (self.map[y][x+1].digged):
				dir.append(east)
			if (self.map[y+1][x].digged):
				dir.append(south)
		return dir 

	def save_map(self, filename):
		f=open(filename, "w")
		for y in self.map:
			s=""
			for x in y:
				if x.digged:
					s+=" "
				else:
					s+="x"
			s+='\n'
			f.write(s)

	def is_digged(self, x, y):
		oob=(x<0) or (x>=self.width) or (y<0) or (y>=self.height)
		if oob:
			return False
		else:
			return self.map[y][x].digged

	def get_distance_exist(self, x, y):
		return math.sqrt(abs(self.exit[0]-y)**2 + abs(self.exit[1]-x)**2)


	def print_rendering(self, win, rendering, light_level):
		#print("\033[1;1H")
		win.clear()
		for y in rendering:
			s=""
			for x in y:
				x=x-light_level
				if x<0:
					x=0
				light=self.light_color[x]
				#s+=win.addstr("\033[48;5;%dm  " % light) # doesn't work
				win.addstr("  ", curses.color_pair(light))
			win.addstr("\n")

	def render(self, x, y):
	# i need two sources of light.. good luck with that
# and i would like the second one to be blue gradiant, and not red gradiant
# fuck you
# if torch close enough
# then we redo another loop
# that will simluate
# and taking account of the surface covered by the first matrice
# i need actually one function, that uses a center, and a gradiant.
# pb : render only output a light level
# looks like the sum of render with a calque applied

	# will render an array of light intensity, from 20 to 0 maybe. array will have a size of 41x41
		max_light=12
		max_distance=5
		light=[[0 for j in range(0, max_distance*2+1)] for i in range(0, max_distance*2+1)]
		angle=0
		array_x=max_distance
		array_y=max_distance
		light[array_y][array_x]=max_light-1
		while angle < math.pi*2:
# calculation
			path=True
			distance=1
			while path and (distance <= max_distance): 
				dx=math.sin(angle)*distance
				dy=math.cos(angle)*distance
				px=round(x+dx) # position in absolute 
				py=round(y+dy) 
				rx=round(array_x+dx) # position in the array of light, relative
				ry=round(array_y+dy) # position in the array of light, relative
				#print("%d %d / %d %d" % (px, py, rx, ry))
				path=self.is_digged(px, py)
				if path:
					new_light=max_light-1-distance
					if light[ry][rx]<new_light:
						light[ry][rx]=new_light
				distance+=1
			angle+=math.pi/50
		# then we change the array for a value from 0 to 1 in float
		return light
		

	def dig(self, x, y):
		self.map[y][x].digged=True

	def dig_v1(self):
	# exit will be whatever wall to the east or south it reaches
		x=0
		y=0
		while (x<self.width) and (y<self.height):
			self.map[y][x].digged=True
			dir=random.choice(self.possible_directions(x, y, True))
			if dir==north:
				y=y-1
			if dir==south:
				y=y+1
			if dir==east:
				x=x+1
			if dir==west:
				x=x-1
		self.exit[0]=y
		self.exit[1]=x

	def render_randomly(self): ## i need a thread here, sadly
		print("\033[2J")
		self.dig_v1()
		light_level=0
		li=self.render(5, 5)
		for i in range(0,50):
			light_level+=(random.randrange(0,2)*2-1)
			if light_level<0:
				light_level=0
			if light_level>3:
				light_level=3
			self.print_rendering(li, light_level)
			time.sleep(0.1)
	
	def dig_v2(self):
		# we create n paths, but one will lead to the exit
		paths=[]
		paths.append([0, 0, self.height - 1, self.width - 1]) # no
		for i in range(0,5):
			paths.append([random.randrange(1, self.height - 1), random.randrange(1, self.width - 1), random.randrange(1, self.height - 1), random.randrange(1, self.width - 1)]) 
		for path in paths:
			y=path[0]
			x=path[0]
			self.dig(x, y)
			print("--------")
			while ((y!=path[2]) and (x!=path[3])):
				dx=path[3]-x
				dy=path[2]-y
				print("dx=%d dy=%d" % (dx, dy))
				print("x=%d y=%d" % (x, y))
				if abs(dx) > abs(dy):
					x+=dx//abs(dx)
				else:
					y+=dy//abs(dy)
				print("x=%d y=%d" % (x, y))
				self.dig(x, y)

def init_curses():
	curses.start_color()
	curses.use_default_colors()
	for i in range(0, curses.COLORS):
		curses.init_pair(i, -1, i); 

def main(win):
	init_curses()
	win.nodelay(True)
	key=""
	win.clear()
	laby=Laby()
	laby.dig_v1()
	laby.save_map('laby.map')
	nx=0
	ny=0
	light_level=0
	win.clear() 
	cont=True
	refresh=True
	played_moved=True
	old_date=datetime.datetime.now()
	i=0
	while cont:		  
		if played_moved:
			x=nx
			y=ny
			li=laby.render(x,y) 
			refresh=True 
			played_moved=False
		new_date=datetime.datetime.now()
		if (new_date-old_date).total_seconds()>1:
			old_date=new_date
			old_light_level=light_level
			light_level+=(random.randrange(0,2)*2-1)
			if light_level<0:
				light_level=0
			if light_level>3:
				light_level=3
			if (light_level!=old_light_level):
				refresh=True 
		time.sleep(0.01) # actually, i should change the light_level if some time passed
# and have another time for the global loop
		if refresh:
			laby.print_rendering(win, li, light_level)
			win.addstr("Distance to exit: %0.2f" % (laby.get_distance_exist(x, y)))
			refresh=False
			i+=1
		key=""
		try:				 
			key = win.getkey()		 
		except:
			pass
		if key=='q':
			cont=False
		if key in ['a', 's', 'd', 'w']:
			dirs=laby.possible_directions(x, y, False)
			if (key=='a') and (west in dirs):
				nx=x-1
			if (key=='d') and (east in dirs):
				nx=x+1
			if (key=='w') and (north in dirs):
				ny=y-1
			if (key=='s') and (south in dirs):
				ny=y+1
			if (ny!=y) or (nx!=x):
				played_moved=True
		if (ny==laby.height-1) or (nx==laby.width-1):
			cont=False

#		except Exception as e:
#			pass		 
	win.nodelay(False)
	win.clear()
	win.addstr("you win")
	win.getkey()



def debug():
	l=Laby()
	#l.dig_v1()
	print(l.possible_directions(10,10, False))

curses.wrapper(main)
#debug()
