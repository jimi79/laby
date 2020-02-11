class Solve(): 
	def __init__(self):
		self.max_iterations = 5000


	def add(self, position, dir_):
		return position[0] + dir_[0], position[1] + dir_[1]

	def solve(self, laby):
		seen = [[False for x in range(0, laby.width)] for y in range(0, laby.height)]
		#directions = [(-1, 0), (0, -1), (1, 0), (0, 1), (1, 1), (1, -1), (-1, -1), (-1, 1)]
		directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
		paths = [[(0, 0)]]
		good_path = None
		while (good_path == None):
			if len(paths) > 1000:
				raise Exception("Lots of paths possible")
			new_paths = []
			for path in paths:
				for d in directions:
					y, x = self.add(path[-1], d)
					if (x == laby.exit[1]) and (y == laby.exit[0]): 
						good_path = path 
						good_path.append((y, x))
						break
					else:
						if y >= 0 and y < laby.height and x >= 0 and x < laby.width:
							if not seen[y][x]: 
								if laby.map[y][x].digged:
									new_paths.append(path + [(y, x)])
									seen[y][x] = True

			paths = new_paths 
		for path in good_path: 
			laby.map[path[0]][path[1]].path = True
		return good_path

