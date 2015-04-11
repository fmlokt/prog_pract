import random
import math

def monte(cycles):
	inner = 0
	for i in range(0,cycles):
		x = random.uniform(-1,1)
		y = random.uniform(-1,1)
		if math.sqrt(x*x + y*y) <=1:
			inner += 1
	
	return (float(inner)/float(cycles) * 4.0)

print monte(100000000)

	
	