#include <iostream>
using namespace std;
class vec{
public:
	double x,y,z;
	vec(double a){
		x=a;
		y=a;
		z=a;
	}
	vec(double a, double b, double c): x(a), y(b), z(c) {}
	void show(){
		cout << "Show Vector: \n";
		cout << '\t' << x << '\t' << y << '\t' << z<< '\n';
	}

};
double scal(vec &a, vec &b){
	return a.x*b.x + a.y*b.y + a.z*b.z;
}

vec vect(vec &a, vec &b){
	return vec(a.y*b.z - b.y*a.z, a.z*b.x - b.z*a.x, a.x*b.y - b.x*a.y);
}


int main(){
	double x,y,z, x1, y1, z1;
	cin >> x >> y >> z;
	cin>> x1 >> y1 >> z1;
	vec v1(x,y,z);
	vec v2(x1, y1, z1);
	vec v3 = vect(v1, v2);
	v1.show();
	v2.show();
	cout << "Inner product \n";
	cout << scal(v1, v2) << '\n';
	cout << "Vector product \n";
	v3.show();
}