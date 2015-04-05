#include <iostream>
using namespace std;
class matrix{
private:
	int n;
	int m;
	double** a;
public:
	 matrix(int N, int M, bool E = 0)
   {
      n = N;
      m = M;
      a = new double *[n];
      for (int i = 0; i < n; ++ i)
      {
         a[i] = new double[m];
         for (int j = 0; j < m; ++ j)
            a[i][j] = (i == j) * E;
      }
   }
void show ()
{
	cout << '\n';
   for (int i = 0; i < n; ++ i)
   {
      for (int j = 0; j < m; ++ j)
         cout << '\t' << a[i][j] ;
   cout << '\n' << '\n';
   }
   cout << '\n';
}
void product()
{
	int k;
	cout << "PRODUCT COEF."; cin >> k;
	for (int i = 0; i < n; ++i)
	for (int j = 0; j < m; ++j)
	a[i][j] *= k;

}
double element(int i, int j){
	return a[i][j];
}
void insert(){
	cout << "MATRIX " << n << " x " << m << '\n' << "ENTER " << m*n << " ELEMENTS" << '\n';
	for (int i = 0; i < n; ++i)
	for (int j = 0; j < m; ++j)
	cin >> a[i][j];
}
~matrix(){if (a) delete a;}
};

int main(){
int n,m;
cout << "N = "; cin >> n;
cout << "M = "; cin >> m;
matrix m1(n,m);
m1.insert();
m1.product();
m1.show();
return 0;
}