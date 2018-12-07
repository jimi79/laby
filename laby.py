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
import numpy

debug=False

east=1
south=2
west=3
north=4


def write_log(s):
	with open("log.log", "a") as f:
		f.write("%s\n" % s)

class Cell:
	def __init__(self):
		self.digged=False
		self.marker=None

class Laby:
	def __init__(self, size=150):
		self.height=size
		self.width=size
		self.max_light_level=12 #index in light_color
		self.max_light_distance=5 # if you increment that, you got to increment the step for each ray 
		self.max_view_distance=12 # if you increment that, you got to increment the step for each ray 
		self.ray_step=30
		self.exit=[-1,-1]
		self.map=[[Cell() for i in range(0, self.width)] for j in range(0, self.height)]
		self.torch_colors=[16,232,233,234,235,52,88,130,172,214,220,226] # 12 redish
		self.exit_colors=[16,232,233,234,235,57,93,135,177,219,225,231] # 12 blueish, only rgb value (from 16 to 255)
# init all colors, laby will handle colors
# rgb is 16+ ((r*16)+g)*16+b
# to decompose : value - 16. / 6, rest is blue. /6, rest is green, int value is red

	def get_possible_directions(self, x, y, digging=False):
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

	def get_view_height(self):
		return (self.max_view_distance*2+1)

	def get_view_width(self):
		if debug:
			return (self.max_view_distance*2+1)*3 # debug
		else:
			return (self.max_view_distance*2+1)*2
		

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


	def print_rendering(self, win, layout_color, layout_text):
		win.move(0, 0)
		for y in range(0, layout_color.shape[0]):
			s=""
			for x in range(0, layout_color.shape[1]):
				color=layout_color[y, x]
				text=layout_text[y][x]
				if text!=None:
					if len(text)==1:
						block=' %s' % text
					else:
						block=text
					#light=min(self.max_light_level-1, light) 
				else:
					block="  "
				#light_color=self.light_colors[light] 
			#	try:
				#color=self.torch_colors[light]
				win.addstr(block, curses.color_pair(color))
				#win.addstr("%03d" % color)
				#except:
				#	raise Exception('error with light %20f' % light)
			win.addstr("\n")

	def render_text(self, x, y):
# i need light. if light < max_light/2, i don't display the number. i actually should pick foreground color here, and leave background as black, and fill with that big white block
# actually, i'll just display the number, and bump up the light
		text=[[None for j in range(0, self.max_view_distance*2+1)] for i in range(0, self.max_view_distance*2+1)]
		text[self.max_view_distance][self.max_view_distance]="<>"
		for dy in range(0, self.max_view_distance*2+1):
			for dx in range(0, self.max_view_distance*2+1):
				px=x-self.max_view_distance+dx
				py=y-self.max_view_distance+dy
				if (px>=0) and (px<self.width) and (py>=0) and (py<self.height):
					marker=self.map[py][px].marker
					if marker!=None:
						if text[dy][dx] is None:
							text[dy][dx]=marker 
		return text

	def render_view(self, povx, povy):
		array_size=self.max_view_distance*2+1
		view=numpy.zeros((array_size, array_size)).astype(int)
		angle=0
		array_center_x=self.max_view_distance # relative center of the view
		array_center_y=self.max_view_distance
		array_abs_top=povx-self.max_view_distance # coordinate of the top left of the array, in absolute
		array_abs_left=povy-self.max_view_distance # coordinate of the top left of the array, in absolute 
		s=""
		while angle < math.pi*2:
			path=True
			distance=0
			while path and (distance <= self.max_view_distance): 
				dx=math.sin(angle)*distance
				dy=math.cos(angle)*distance
				abs_x=round(povx+dx) # position in absolute 
				abs_y=round(povy+dy) 
				array_x=abs_x-array_abs_top
				array_y=abs_y-array_abs_left 
				path=self.is_digged(abs_x, abs_y)
				if debug:
					s+='%d %d ' % (abs_x, abs_y)
				if array_x>=0 and array_x<array_size and array_y>=0 and array_y<array_size:
					if path:
						view[array_y, array_x]=1
# things i've tried here and didn't work
# add light each time the ray come across the cell:
# light+=max_light/100
# so the further away i am, the less ray will go on the cell
# -> didn't look good
#
# add light if no path (meaning light bumps on the wall) -> display less readable 
				distance+=1
			angle+=math.pi/self.ray_step
		return view 

	def render_light(self, povx, povy, lx, ly, ignore_wall_length=0, view=None):
# render the light for one light source
# povx povy: point of view
# lx ly: light source 
# ignore_wall_length: light pass through walls for that distance, 0=no 
		array_size=self.max_view_distance*2+1
		light=numpy.zeros((array_size, array_size)).astype(int)
		angle=0
		array_center_x=self.max_view_distance # relative center of the view
		array_center_y=self.max_view_distance
		array_abs_top=povx-self.max_view_distance # coordinate of the top left of the array, in absolute
		array_abs_left=povy-self.max_view_distance # coordinate of the top left of the array, in absolute

		distance=math.sqrt((povx-lx)**2+(povy-ly)**2)
		if distance < (self.max_view_distance+self.max_light_distance): 
#if we look at a light that can emit to distance x, and we can see up to distance y, then we don't render anythg if sum is < distance of calculation
			while angle < math.pi*2:
				path=True
				distance=0
				while path and (distance <= self.max_light_distance): 
					dx=math.sin(angle)*distance
					dy=math.cos(angle)*distance
					abs_x=round(lx+dx) # position in absolute 
					abs_y=round(ly+dy) 
					array_x=abs_x-array_abs_top
					array_y=abs_y-array_abs_left 
					path=self.is_digged(abs_x, abs_y) or distance<ignore_wall_length
					if array_x>=0 and array_x<array_size and array_y>=0 and array_y<array_size:
						if path:
							light[array_y, array_x]=self.max_light_level-1-distance
# things i've tried here and didn't work
# add light each time the ray come across the cell:
# light+=max_light/100
# so the further away i am, the less ray will go on the cell
# -> didn't look good
#
# add light if no path (meaning light bumps on the wall) -> display less readable 
					distance+=1
				angle+=math.pi/50
			light=light.round().astype(int)
		return light

	def write_matrice_debug_file(self, mat, filename="debug.csv"):
		numpy.savetxt(filename, mat, fmt="%3d")

	def apply_color_on_layer(self, layer, array):
		for y in range(0, layer.shape[0]):
			for x in range(0, layer.shape[0]):
				layer[y,x]=array[layer[y,x]]

	def get_max_level_light(self, layer):
		wlevel=(layer>=232)*layer
		left=(layer<232)*(layer>=16)*layer-16 # we smply ignore the legaly colors
		r1=left//36
		g1=(left-r1*36)//6
		b1=left % 6
		level=numpy.maximum(r1/6, g1/6, b1/6)/6 
		level=numpy.maximum(level, wlevel/24)/6 
		return level
	

	def rgb(self, layer):
		wlevel=(layer>=232)*layer/24
		left=(layer<232)*(layer>=16)*layer-16 # we smply ignore the legaly colors
		r1=left//36
		lr1=r1/6
		g1=(left-r1*36)//6
		lg1=g1/6
		b1=left % 6
		lb1=b1/6
		level=numpy.maximum(lr1, lg1, lb1)/6 
		return r1, g1, b1, level, wlevel

	def merge_layer_by_strength(self, layer1, layer2, strength_layer1_toward_layer2=0.5):
		if numpy.max(layer1)==0:
			write_log('1')
			return layer2
		else:
			if numpy.max(layer2)==0: # i should go here
				write_log('2')
				return layer1
			else: 
				write_log('3')
				level1=self.get_max_level_light(layer1) 
				level2=self.get_max_level_light(layer2) 
				result=(level1*strength_layer1_toward_layer2>level2)*layer1+(level1*strength_layer1_toward_layer2<=level2)*layer2 
				result=result.astype(int)
				return result

	def merge_layer_by_absence(self, layer1, layer2):
		return (layer1*(layer2==16)+layer2*(layer2!=16)).astype(int)


	def render_lights(self, povx, povy, lx, ly, light_level=0, light_on=True):
		if light_on:
			light=self.render_light(povx, povy, lx, ly)
			light=light-light_level # torch flicker 
			# then we apply the color on that layer
			light=numpy.maximum(0, light)
			self.apply_color_on_layer(light, self.torch_colors)


		light_exit=self.render_light(povx, povy, self.exit[1], self.exit[0], ignore_wall_length=0)
		view=self.render_view(povx, povy)
		light_exit=light_exit*view
		self.apply_color_on_layer(light_exit, self.exit_colors)

		if light_on:
			#light=numpy.maximum(light, light_exit)  # wrong
			light=self.merge_layer_by_absence(light, light_exit)
		else:
			light=light_exit

		return light
		
	def place_object(self, obj, x, y):
		self.map[y][x].marker=obj

	def remove_object(self, x, y):
		self.map[y][x].marker=None

	def dig(self, x, y):
		self.map[y][x].digged=True

	def dig_clear(self):
		for i in range(0, len(self.map)-1):
			for j in range(0, len(self.map)-1):
				self.map[i][j].digged=True
		self.exit[0]=self.height-2
		self.exit[1]=self.width-2
		write_log("%d %d" % (self.exit[0], self.exit[1]))
		self.map[self.exit[1]][self.exit[0]].digged=True

	def dig_v1(self):
		if debug:
			self.dig_clear() #debug
			return
	# exit will be whatever wall to the east or south it reaches
		x=0
		y=0
		last_dir=None
		while (x<self.width-1) and (y<self.height-1):
			self.map[y][x].digged=True 
			if last_dir==None or (random.randrange(1,3)==1):
				dir=random.choice(self.get_possible_directions(x, y, True))
			else:
				dir=last_dir
				if not(dir in self.get_possible_directions(x, y, True)):
					dir=random.choice(self.get_possible_directions(x, y, True)) 
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
		dirs=self.get_possible_directions(x, y, False)
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
		self.old_s=''

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

	def init_colors(self):
		curses.start_color()
		curses.use_default_colors()

		for i in range(0, 256):
			curses.init_pair(i, 0, i);

	def add_help_window(self):
		win2=curses.newwin(20, 30, 3, self.laby.get_view_width()+2)
		win2.addstr('wasd to move once\n', )
		win2.addstr('WASD to move and keep moving\n')
		win2.addstr('1 to 9 to drop marker\n')
		win2.addstr('0 to remove markers\n')
		win2.addstr('l to turn on/off the light\n')
		win2.addstr('o to automatically walk to the exit\n')
		win2.addstr('q to quit\n')
		win2.refresh()
		self.win2=win2
		return win2 

	def set_hint(self, s):
		self.win2.move(10,0)
		self.win2.addstr(''.join([' ' for i in range(0, len(self.old_s))]))
		self.win2.move(10,0)
		self.win2.addstr(s)
		self.win2.refresh()
		self.old_s=s

	def init_laby(self, win):
		win.erase()
		win.move(5,2);
		win.addstr('please wait...');
		win.refresh()
		self.laby=Laby(self.size)
		self.laby.dig_v1()
		#self.laby.dig_clear()
		self.laby.save_map('laby.map')
		win.erase() 
	
	def main(self, win):
		self.init_colors()
		self.init_laby(win) # will define a self.laby, win is sent to display 'please wait'
		win.resize(max(self.laby.get_view_height()+1, 10), max(self.laby.get_view_width()+1, 30))
		key=""
		win2=self.add_help_window() 
		win2.refresh()
		#win.nodelay(True)
		curses.halfdelay(1)
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
		player_auto=None
		light=True
		first_run=False
		while cont:		  
			if (x==self.laby.exit[1]) and (y==self.laby.exit[0]):
				cont=False # he wins 
			else:
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

				if player_direction is None and player_auto:
					new_running_last_step=datetime.datetime.now()
					if first_run or ((new_running_last_step-old_running_last_step).total_seconds()>0.1): 
						old_running_last_step=new_running_last_step
						d=self.laby.get_possible_directions(x, y, False)
						if x<self.laby.exit[1] and (east in d):
							x+=1
							refresh=True
						elif y<self.laby.exit[0] and (south in d):
								y+=1
								refresh=True
						elif y>self.laby.exit[0] and (north in d):
							y-=1
							refresh=True
						elif x>self.laby.exit[1] and (west in d):
								x-=1
								refresh=True
						else:
							player_auto=False 
							self.set_hint('')

# did the player put an object on the map
				if new_object:
					te=self.laby.render_text(x,y) 
					refresh=True 
					new_object=False 

# does the torch want to change its luminescence
				if not debug:
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
					li=self.laby.render_lights(x, y, x, y, light_level=light_level, light_on=light) 
					self.laby.print_rendering(win, li, te)
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
					if key=='l':
						light=not light
						refresh=True
					elif key=='q':
						cont=False # exit, would requires some sort of confirmation though
					elif key=='o':
						player_auto=not player_auto # display that somewhere 
						if player_auto:
							self.set_hint('auto mode')
						else:
							self.set_hint('')
					else:
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
			dirs=laby.get_possible_directions(x, y, False) 
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

