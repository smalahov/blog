struct Base1 {
    long int B1 = 0xB1;
    virtual long int Sum1(int a) {
        return B1 + a;
    }
};

struct Base2 {
    long int B2 = 0xB2;
    virtual long int Sum2(int a) {
        return B2 + a;
    }
};

struct Derived: Base1, Base2 {
    long int D = 0x0D0;
    long int Sum2(int a) override {
        return D + B2 + a;
    }
};

int main() {
    Derived d;
    Base2& db = d;
    return d.Sum2(1) + db.Sum2(2);
}
