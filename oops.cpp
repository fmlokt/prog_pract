#include <iostream>
#include <time.h>
#include <stdlib.h>
#include <unistd.h>
using namespace std;
class prng{
public:
	int max;
	int state[8];
	int res;
	void iterate(void);

	prng(){
		res = (time(0)<<16) + getpid();
	}
//	int operator int ();
};

//int prng::operator int(){
//	iterate();
//	return state[7] %max;
//}

int main()
{
	prng a;
	int b;
//	cout << a.res << endl;
	for (int i = 0; i < 100; i++){
		b = (time(0)<<16) + getpid();
		cout << b << endl;}
	return 0;
}