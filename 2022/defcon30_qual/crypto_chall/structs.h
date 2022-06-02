#include <string>
#include <memory>

using namespace std;

class IKey {
public:
  virtual void create(string key1) = 0;
  virtual string encrypt() = 0;
  virtual string decrypt() = 0;
};

struct num;  // some bigint

struct key_pair {
  shared_ptr<num> *p;
  shared_ptr<num> *q;
  void *sub_d53a;
  void *sub_d4c4; // optimization
};

class rsa_key : IKey {
  int key_len;
  int used;
  key_pair kp;
  shared_ptr<num> e;
  shared_ptr<num> inv;
  shared_ptr<num> modulus;

public:
  rsa_key() : key_len(0), used(0) {}
};  

constexpr unsigned int s = sizeof(key_pair);