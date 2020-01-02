from World import *
import threading

world = World(8, 8)

world.map.add_obstacle(4, 5)
world.map.add_obstacle(4, 4)
world.map.add_obstacle(2, 4)
world.map.add_obstacle(3, 4)
world.map.add_obstacle(4, 0)
world.map.add_obstacle(4, 1)
world.map.add_obstacle(4, 2)
world.map.add_obstacle(4, 3)

world.map.add_cat(6, 6)
world.map.add_cheese(6, 1)

t = threading.Thread(target=world.run)
t.daemon = True
t.start()

world.start()
