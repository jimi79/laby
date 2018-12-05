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
import argparse


east=1
south=2
west=3
north=4

class Cell:
	def __init__(self):
		self.digged=False
		self.marker=None

class Laby:
	def __init__(self, size=150):
		self.height=size
		self.width=size
		self.max_light=13 #index in light_color
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
		#win.clear() 
		win.move(1,1)
		for y in range(0, len(layout_light)):
			s=""
			for x in range(0, len(layout_light[0])):
				light=layout_light[y][x]-light_level
				if light<0:
					light=0
				text=layout_text[y][x]
				if text!=None:
					if len(text)==1:
						block=' %s' % text
					else:
						block=text
					light=min(self.max_light-1, light) 
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

	def render_light(self, povx, povy, lx, ly):
# render the light for one light source
# povx povy: point of view
# lx ly: light source


		array_size=self.max_distance*2+1
		light=[[0 for j in range(0, array_size)] for i in range(0, array_size)] 

# first : distance between light and center. if too big, then no point of doing anythg

		angle=0
		array_center_x=self.max_distance # relative center of the view
		array_center_y=self.max_distance
		array_abs_top=povx-self.max_distance # coordinate of the top left of the array, in absolute
		array_abs_left=povy-self.max_distance # coordinate of the top left of the array, in absolute

		#light[self.max_distance][self.max_distance]=self.max_light-1 # center of the array
		while angle < math.pi*2:
# calculation
			path=True
			distance=0
			while path and (distance <= self.max_distance): 
				dx=math.sin(angle)*distance
				dy=math.cos(angle)*distance
				abs_x=round(lx+dx) # position in absolute 
				abs_y=round(ly+dy) 

				# i have to find out 
				array_x=abs_x-array_abs_top
				array_y=abs_y-array_abs_left 

				#print("%d %d / %d %d" % (px, py, rx, ry))
				path=self.is_digged(abs_x, abs_y)
				if array_x>=0 and array_x<array_size and array_y>=0 and array_y<array_size:
					if path:
						light[array_y][array_x]=self.max_light-1-distance
# things i've tried here and didn't work
# add light each time the ray come across the cell:
# light+=max_light/100
# so the further away i am, the less ray will go on the cell
# -> didn't look good
#
# add light if no path (meaning light bumps on the wall) -> display less readable 
				distance+=1
			angle+=math.pi/50
		# then we change the array for a value from 0 to 1 in float

		light=[[min(round(i), self.max_light-1) for i in x] for x in light]

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
		last_dir=None
		while (x<self.width-1) and (y<self.height-1):
			self.map[y][x].digged=True 
			if last_dir==None or (random.randrange(1,2)==1):
				dir=random.choice(self.possible_directions(x, y, True))
			else:
				dir=last_dir
				if not(dir in self.possible_directions(x, y, True)):
					dir=random.choice(self.possible_directions(x, y, True)) 
			last_dir=dir 
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
		self.exit[0]=y
		self.exit[1]=x
		self.map[y][x].marker='[]'

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

	def can_go(self, x, y, direction): 
		dirs=self.possible_directions(x, y, False)
		if direction in dirs:
			if direction==north:
				y-=1
			if direction==south:
				y+=1
			if direction==east:
				x+=1
			if direction==west:
				x-=1
			return True, x, y
		else:
			return False, x, y

class CursesGame(): 
	def __init__(self):
		self.laby=None
		self.size=300

	def check_key(self, key):
		direction=None
		continuous=None
		item_left=None
		if key!='':
			if key.lower()=='w':
				direction=north
			if key.lower()=='s':
				direction=south
			if key.lower()=='a':
				direction=west
			if key.lower()=='d':
				direction=east
			if key in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
				if key=='0':
					item_left=""
				else:
					item_left=key
			continuous=key.upper()==key
		return direction, continuous, item_left

	def write_log(self, s):
		with open("log.log", "a") as f:
			f.write("%s\n" % s)

	def init_colors(self):
		curses.start_color()
		curses.use_default_colors()

		light_colors=[0,232,233,234,235,52,88,130,172,214,220,226,15] # 13
		for i in range(0, len(light_colors)):
			curses.init_pair(i+1, 0, light_colors[i]); 

	def add_help_window(self):
		win2=curses.newwin(20, 40, 0, 41)
		win2.addstr('wasd to move once\n')
		win2.addstr('WASD to move and keep moving\n')
		win2.addstr('1 to 9 to drop marker\n')
		win2.addstr('0 to remove markers\n')
		win2.addstr('q to quit\n')
		win2.refresh()
		return win2 

	def init_laby(self, win):
		win.clear()
		win.move(5,2);
		win.addstr('please wait...');
		win.refresh()
		self.laby=Laby(self.size)
		self.laby.dig_v1()
		self.laby.save_map('laby.map')
		win.clear()

	
	def main(self, win):
		self.init_colors()
		self.init_laby(win) # will define a self.laby, win is sent to display 'please wait'
		key=""
		win=curses.newwin(30, 40, 0, 0)
		self.add_help_window() 
		win.nodelay(True)
		curses.curs_set(False) 
		x=0
		y=0
		light_level=0
		cont=True # global loop
		old_date=datetime.datetime.now() # last time the torch's light changed
		new_object=False # a new object was placed or an object was removed, refresh the display
		refresh=True # refresh the display
		player_direction=None # player move (north, east, etc). may be impossible
		player_running_direction=None # not stopping after doing one step
		te=self.laby.render_text(x,y) # first time, we do it manually
		old_running_last_step=datetime.datetime.now()
		first_run=False
		while cont:		  
			time.sleep(0.01) # cpu usage 
			if (x==self.laby.exit[1]) and (y==self.laby.exit[0]):
				cont=False # he wins 
# is the player running
			if player_running_direction!=None:
				new_running_last_step=datetime.datetime.now()
				if first_run or ((new_running_last_step-old_running_last_step).total_seconds()>0.1): 
					old_running_last_step=new_running_last_step
					player_direction=player_running_direction
					first_run=False
				else:
					player_direction=None 

# does the player want to move
			if player_direction!=None:
				can_go, x, y=self.laby.can_go(x, y, player_direction)
				if can_go:
					refresh=True
				else:
					player_running_direction=None
				if player_running_direction==None:
					player_direction=None # if not running, stopping after one step
				
				te=self.laby.render_text(x,y) 
				refresh=True 
				player_moved=False

# did the player put an object on the map
			if new_object:
				te=self.laby.render_text(x,y) 
				refresh=True 
				new_object=False 

# does the torch want to change its luminescence
			new_date=datetime.datetime.now()
			if (new_date-old_date).total_seconds()>0.3: 
				old_date=new_date
				old_light_level=light_level
				light_level+=(random.randrange(0,2)*2-1)
				if light_level<0:
					light_level=0
				if light_level>3:
					light_level=3
				if (light_level!=old_light_level):
					refresh=True 

# after all these events, is there one that requires us to redo the display
			if refresh:
				li=self.laby.render_light(x, y, x, y) 
				self.laby.print_rendering(win, li, te, light_level)
				win.addstr("Distance to exit: %0.2f   " % (self.laby.get_distance_exist(x, y)))
				win.refresh()
				refresh=False
			key=""
			try:				 
#			pass
				key = win.getkey()		 
			except:
				pass

			# key presseed
			if key != '':
				if key=='q':
					cont=False # exit, would requires some sort of confirmation though
				direction, is_player_running, item_left=self.check_key(key)
				if direction!=None:
					if is_player_running:
						player_running_direction=direction
						player_direction=None
						old_running_last_step=datetime.datetime.now() # last time the player stepped while running, we initialse at now to match the before-while initialisation. Anyway first_run is at true
						first_run=True # first run, because first time we don't wait the time delta
					else:
						player_direction=direction
						player_running_direction=None
				if item_left!=None:
					self.laby.map[y][x].marker=item_left
					new_object=True

class BinaryGame:

	def __init__(self):
		self.array_dir_to_bin={4:1, 1:2, 2:4, 3:8}
		self.array_bin_to_dir={1:4, 2:1, 4:2, 8:3}
		self.size=10

	def dir_to_bin(self, dirs):
		a=0
		for dir_ in dirs:
			a+=self.array_dir_to_bin[dir_]
		return a

	def play(self):
		laby=Laby(self.size)
		print("please wait, building the map...")
		laby.dig_v1()
		print("done")
		laby.save_map('laby.map')
		x=0
		y=0
		cont=True
		print("1=north, 2=east, 4=south, 8=west. sum in binary is the directions you can take. q to quit")
		while ((x!=laby.exit[1]) or (y!=laby.exit[0])) and cont:
			dirs=laby.possible_directions(x, y, False) 
			print("possible directions: %d, distances: %0.2f" % (self.dir_to_bin(dirs), laby.get_distance_exist(x, y)))
			dir_=input("what direction do you chose ? ")
			if dir_=="q":
				cont=False
			else:
				idir=None
				try:
					idir=int(dir_)
				except ValueError:
					idir=None
				if idir==None:
					print("Unknown direction, 'q' to quit")
				else:
					idir=self.array_bin_to_dir[idir]
					if not(idir in dirs):
						print("Cannot go there")
					else:
						if idir==north:
							y-=1
						if idir==south:
							y+=1
						if idir==east:
							x+=1
						if idir==west:
							x-=1
		if cont:
			print("you reach the exit")
		else:
			print("you quit")


parser=argparse.ArgumentParser(description="Labyrinth")
parser.add_argument('--binary', action='store_const', dest='binary', help='play in binary', const=True)
parser.add_argument('--size', help='size of the laby (default 150)', type=int, default=150)
args=parser.parse_args()
if args.binary:
	a=BinaryGame()
	a.size=args.size
	a.play()
else:
	a=CursesGame()
	a.size=args.size
	curses.wrapper(a.main)
#debug()

