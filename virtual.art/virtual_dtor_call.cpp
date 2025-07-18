struct Base {
    virtual int Sum(int a, int b) {
        return a + b;
    }

    ~Base() {
        Sum(1,1);
    }
};

struct Derived: Base {
    int Sum(int a, int b) override {
        return a * 2 + b;
    }

    ~Derived() {
        Sum(1,1);
    }
};

int main() {
    Derived d;
    return d.Sum(1, 2);
}
