struct Base {
    long long A = 0x0B0;
    virtual int Sum(int a) {
        return A + a;
    }
};

struct Derived: Base {
    long long B = 0x0D0;
};

struct MoreDerived: Derived {
    long long C = 0x0D1;

    int Sum(int a) override {
        return A + B + C + a;
    }
};

int main() {
    return 0;
}
