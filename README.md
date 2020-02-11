To start: run.py

This is a top down view labyrinth.
You're in some cave, and have to find an exit somewhere.

The view is a top down view of you, on a 2d labyrinth.
The view is centered on you. You're holding a torch emitting light.

The lightest point is you.
If there is no wall, the light goes darker and darker in every direction.
If there is a wall, the light is stopped.
A wall hides everythg behind it.

You move with usual wasd keys.

You can add markers with keys from 1 to 9.
A marker is useful if u want for example leave a mark reminding you that path has no end.
You can remove a marker with key 0.

The distance to the exit is shown below the map.

When the exit is reached, the program exits. You can also quit with letter q.
When you restart, a new map is generated.

A file, laby.map, is generated once you finish the game (or at start in binary mode).
A colored version is also generated, laby_256.map. i suggest less -R -S laby_256.map to see it.

You can also change settings, check with -h options
