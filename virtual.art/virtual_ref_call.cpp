struct Base {
    virtual int Sum(int a, int b) {
        return a + b;
    }
};

struct Derived: Base {
    int Sum(int a, int b) override {
        return a * 2 + b;
    }
};

int main() {
    Derived d;
    Base& b = d;
    return b.Sum(1, 2);
}
