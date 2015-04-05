def fib(n):
    if n < 2:
        return n
    return fib(n-2) + fib(n-1)


def euk(x,y):
	
	if x>y:
		return euk(x-y, y)
		
	if x<y:
		return euk(x, y-x)
		
	if x == y:
		return x

print euk(462, 1071)
print ('------')
print fib(10)
print fib(20)
print fib(30)
