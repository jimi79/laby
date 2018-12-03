#!/usr/bin/env python3

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
		self.height=150
		self.width=150
		self.max_light=11 #index in light_color
		self.max_distance=5
		self.exit=[-1,-1]
		self.map=[[Cell() for i in range(0, self.width)] for j in range(0, self.height)]
		#self.light_colors=[0,232,233,234,235,52,88,130,172,214,220,226] # 13

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


	def print_rendering(self, win, layout_light, layout_text, light_level):
		win.clear() 
		for y in range(0, len(layout_light)):
			s=""
			for x in range(0, len(layout_light[0])):
				light=layout_light[y][x]-light_level
				if light<0:
					light=0
				text=layout_text[y][x]
				if text!=None:
					block=' %s' % text
					light=min(self.max_light, light) 
				else:
					block="  "
				#light_color=self.light_colors[light] 
				win.addstr(block, curses.color_pair(light+1))
			win.addstr("\n")

	def render_text(self, x, y):
# i need light. if light < max_light/2, i don't display the number. i actually should pick foreground color here, and leave background as black, and fill with that big white block
# actually, i'll just display the number, and bump up the light
		text=[[None for j in range(0, self.max_distance*2+1)] for i in range(0, self.max_distance*2+1)]
		for dy in range(0, self.max_distance*2+1):
			for dx in range(0, self.max_distance*2+1):
				px=x-self.max_distance+dx
				py=y-self.max_distance+dy
				if (px>=0) and (px<self.width) and (py>=0) and (py<self.height):
					marker=self.map[py][px].marker
					if marker!=None:
						text[dy][dx]=marker 
		return text

	def render_light(self, x, y):
		light=[[0 for j in range(0, self.max_distance*2+1)] for i in range(0, self.max_distance*2+1)]
		angle=0
		array_x=self.max_distance
		array_y=self.max_distance
		light[array_y][array_x]=self.max_light-1
		while angle < math.pi*2:
# calculation
			path=True
			distance=1
			while path and (distance <= self.max_distance): 
				dx=math.sin(angle)*distance
				dy=math.cos(angle)*distance
				px=round(x+dx) # position in absolute 
				py=round(y+dy) 
				rx=round(array_x+dx) # position in the array of light, relative
				ry=round(array_y+dy) # position in the array of light, relative
				#print("%d %d / %d %d" % (px, py, rx, ry))
				path=self.is_digged(px, py)
				if path:
					new_light=self.max_light-1-distance
					if light[ry][rx]<new_light:
						light[ry][rx]=new_light
				distance+=1
			angle+=math.pi/50
		# then we change the array for a value from 0 to 1 in float
		return light
		
	def place_object(self, obj, x, y):
		self.map[y][x].marker=obj

	def remove_object(self, x, y):
		self.map[y][x].marker=None

	def dig(self, x, y):
		self.map[y][x].digged=True

	def dig_v1(self):
	# exit will be whatever wall to the east or south it reaches
		x=0
		y=0
		while (x<self.width-1) and (y<self.height-1):
			self.map[y][x].digged=True
			dir=random.choice(self.possible_directions(x, y, True))
			old_x=x
			old_y=y
			if dir==north:
				y=y-1
			if dir==south:
				y=y+1
			if dir==east:
				x=x+1
			if dir==west:
				x=x-1
		self.map[y][x].digged=True
		self.exit[0]=old_y
		self.exit[1]=old_x

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

	light_colors=[0,232,233,234,235,52,88,130,172,214,220,226] # 13
	for i in range(0, len(light_colors)):
		curses.init_pair(i+1, 0, light_colors[i]); 

def main(win):
	init_curses()
	key=""
	win=curses.newwin(12, 28, 0, 0)
	win.clear()
	win2=curses.newwin(20, 30, 0, 30)
	win2.addstr('wasd to move\n')
	win2.addstr('1 to 9 to drop markers\n')
	win2.addstr('0 to remove markers\n')
	win2.addstr('q to quit\n')
	win2.refresh()

	win.nodelay(True)

	laby=Laby()
	laby.dig_v1()
	laby.save_map('laby.map')
	nx=0
	ny=0
	light_level=0
	win.clear() 
	cont=True
	refresh=True
	player_moved=True
	old_date=datetime.datetime.now()
	i=0
	new_object=False
	while cont:		  
		time.sleep(0.01) # cpu usage
		if player_moved:
			x=nx
			y=ny
			te=laby.render_text(x,y) 
			refresh=True 
			player_moved=False
		if new_object:
			te=laby.render_text(x,y) 
			refresh=True 
			new_object=False 

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

		if refresh:
			li=laby.render_light(x,y) 
			laby.print_rendering(win, li, te, light_level)
			win.addstr("Distance to exit: %0.2f" % (laby.get_distance_exist(x, y)))
			win.refresh()
			refresh=False
			i+=1
		key=""
		try:				 
			key = win.getkey()		 
		except:
			pass
		if key=='q':
			cont=False
		if key in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
			laby.place_object(key, x, y)
			new_object=True
		if key=='0':
			laby.remove_object(x, y)
			new_object=True
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
				player_moved=True
		if (ny==laby.height-1) or (nx==laby.width-1):
			cont=False

#		except Exception as e:
#			pass		 
	#win.nodelay(False)
	#win.clear()
	#win.addstr("you win")
	#win.getkey()



def debug():
	l=Laby()
	#l.dig_v1()
	print(l.possible_directions(10,10, False))

curses.wrapper(main)
#debug()
