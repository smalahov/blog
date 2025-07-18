struct Base {
    int Sum(int a, int b) {
        return a + b;
    }
};

int main() {
    Base b;
    return b.Sum(1, 2);
}
