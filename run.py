#!/usr/bin/python3

from laby import *

parser = argparse.ArgumentParser(description = "Labyrinth")
parser.add_argument('--binary', action = 'store_const', dest = 'binary', help = 'play in binary', const = True)
parser.add_argument('--dig', help = 'digging method: 1 or 2', type = int, default = 1)
parser.add_argument('--test', action = 'store_const', dest = 'test', help = "programmer's test", const = True)
parser.add_argument('--size', help = 'size of the laby (default 150)', type = int, default = 150)
args = parser.parse_args()

if args.test:
	test()
else:
	print("please wait, building labyrinth")
	laby = Laby(args.size)
	if args.dig == 1:
		laby.dig_v1()
	if args.dig == 2:
		laby.dig_v2()
	if args.binary:
		laby.save_map('laby.map')
		a = BinaryGame(laby)
		a.play()
	else:
		a = CursesGame(laby)
		curses.wrapper(a.main)
		laby.save_map('laby.map')
		laby.save_map_256('laby_256.map')

