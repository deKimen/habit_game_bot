# test_matplotlib.py
import sys

print("Python path:", sys.path)

try:
    import matplotlib

    print(f"✅ matplotlib version: {matplotlib.__version__}")

    import matplotlib.pyplot as plt

    print("✅ pyplot imported")

    # Простой тест
    plt.figure()
    plt.plot([1, 2, 3], [4, 5, 6])
    plt.savefig('test_plot.png')
    print("✅ График создан успешно!")

except Exception as e:
    print(f"❌ Ошибка: {e}")