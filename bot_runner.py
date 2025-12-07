#!/usr/bin/env python3
"""
Файл для запуска бота на PythonAnywhere
"""
import sys
import os

from app.main import main

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
if __name__ == "__main__":
    print("Запуск бота на PythonAnywhere...")
    main()
