# habit_game_bot

Telegram-бот для отслеживания привычек с RPG-механиками. 
Прокачивайте персонажа, выполняя задания и вырабатывая полезные привычки в реальной жизни!

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![python-telegram-bot](https://img.shields.io/badge/Telegram%20Bot-20.7-green.svg)](https://python-telegram-bot.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-orange.svg)](https://sqlalchemy.org)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.5-yellow.svg)](https://pydantic-docs.helpmanual.io)

# О проекте
Habit Game Bot превращает скучное отслеживание привычек в увлекательную RPG-игру! 
Создайте персонажа и прокачивайте его характеристики, выполняя реальные задания:
- Сила - физические привычки (спорт, зарядка)
- Ловкость - навыковые привычки (игра на инструменте, рисование)  
- Интеллект - обучающие привычки (чтение, учёба)
- Харизма - социальные привычки (общение, встречи)

# Возможности
# Основной функционал
- Создание персонажа с уникальными характеристиками
- Управление привычками (добавление, выполнение, отслеживание)
- Система прокачки - уровень, опыт, характеристики
- Статистика и аналитика прогресса
- Игровые уведомления и мотивация

# Игровые механики
- Система достижений и наград
- Серии выполнения
- Визуализация прогресса
- Кастомизация персонажа

# Быстрый старт
# Предварительные требования
- Python 3.9+
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))
- SQLite (встроенная) или PostgreSQL

# Установка
1. **Клонирование репозитория:**
bash
git clone https://github.com/yourusername/habit-gamification-bot.git
cd habit-gamification-bot

2. Создание виртуального окружения:
bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
# или
venv\Scripts\activate     # Windows

3. Установка зависимостей:
bash
pip install -r requirements.txt

4. Настройка окружения:
bash
cp .env.example .env

#Отредактируйте .env файл:
env
BOT_TOKEN=your_telegram_bot_token_here
DATABASE_URL=sqlite:///habits.db
DEBUG=False

5. Инициализация базы данных:
bash
python -m app.db.init_db

6. Запуск бота:
bash
python -m app.main

# Использование
# Основные команды:

- /start - Начать работу, создать персонажа
- /newhabit - Добавить новую привычку
- /habits - Показать текущие привычки
- /done <ID> - Отметить привычку выполненной
- /stats - Статистика персонажа
- /achievements - Достижения
- /help - Помощь по командам


# Пример использования:
Пользователь:   /start
Бот:   Добро пожаловать в HabitRPG! 
       Создаю твоего персонажа...
       Твой персонаж создан!
       Уровень: 1
       Опыт: 0/100
       Сила: 1
       Ловкость: 1
       Интеллект: 1
       Харизма: 1
Пользователь:  /newhabit
Бот:           Какую привычку хотите добавить?
Пользователь:  Утренняя зарядка
Бот:   Выберите тип привычки:
       1. Ежедневная
       2. Еженедельная  
       3. Произвольная
Пользователь: 1
Бот:          Какая характеристика прокачивается?
              Сила - физические активности
              Ловкость - навыки и координация
              Интеллект - обучение и чтение
              Харизма - общение и творчество
Пользователь: Сила
Бот:          Привычка "Утренняя зарядка" добавлена!
              ID: 1 
              Награда: 10 опыта, +1 к Силе
Пользователь: /done 1
Бот:          Привычка "Утренняя зарядка" выполнена!
              +10 опыта, +1 к Силе
              Серия: 1 день подряд
              Достижение: "Первые шаги" разблокировано!

# Архитектура проекта

habit-gamification-bot/
├── app/
│   ├── init.py
│   ├── main.py                 # Точка входа
│   ├── bot/
│   │   ├── init.py
│   │   ├── handlers.py         # Обработчики команд
│   │   └── keyboards.py        # Клавиатуры
│   ├── core/
│   │   ├── init.py
│   │   ├── config.py           # Конфигурация
│   │   └── security.py         # Безопасность
│   ├── db/
│   │   ├── init.py
│   │   ├── database.py         # Подключение к БД
│   │   ├── models.py           # SQLAlchemy модели
│   │   └── init_db.py          # Инициализация БД
│   ├── services/
│   │   ├── init.py
│   │   ├── user_service.py     # Работа с пользователями
│   │   ├── habit_service.py    # Управление привычками
│   │   ├── game_service.py     # Игровая логика
│   │   └── notification.py     # Уведомления
│   ├── models/
│   │   ├── init.py
│   │   ├── schemas.py          # Pydantic схемы
│   │   └── domain.py           # Бизнес-модели
│   └── utils/
│       ├── init.py
│       ├── validators.py       # Валидация
│       └── formatters.py       # Форматирование
├── tests/
│   ├── init.py
│   ├── conftest.py
│   ├── test_handlers.py
│   ├── test_services.py
│   └── test_models.py
├── requirements.txt
├── .env.example
└── README.md

# Модели данных
Основные сущности:
python
@dataclass
class User:
    id: int
    telegram_id: int
    username: str
    character: Character
    habits: List[Habit]
    created_at: datetime

@dataclass  
class Character:
    level: int
    experience: int
    strength: int
    agility: int
    intelligence: int
    charisma: int
    achievements: List[Achievement]

@dataclass
class Habit:
    id: int
    name: str
    habit_type: HabitType
    frequency: int
    current_streak: int
    best_streak: int
    stat_bonus: StatType
    xp_reward: int
    created_at: datetime

# План разработки
# Итерация 1
Основные фичи:
· Система пользователей и персонажей
· CRUD операции для привычек
· Базовая игровая механика (опыт, уровни)
· Команды бота (/start, /newhabit, /done, /stats)
Фича от ассистента: [будет добавлена после согласования]

# Итерация 2 
Основные фичи:
· Система достижений и наград
· Детальная аналитика прогресса
· Умные напоминания и мотивация
· Кастомизация персонажа
Фича от ассистента: [будет добавлена после согласования]

# Tестирование
bash
# Запуск всех тестов
pytest

# Запуск с покрытием
pytest --cov=app tests/

# Запуск конкретного модуля
pytest tests/test_habit_service.py -v

# Генерация отчёта о покрытии
pytest --cov=app --cov-report=html tests/

# Технологии
· Python 3.9+ - основной язык
· python-telegram-bot - работа с Telegram API
· SQLAlchemy - ORM для работы с БД
· Pydantic - валидация данных
· Alembic - миграции базы данных
· pytest - тестирование
· SQLite/PostgreSQL - база данных

# Разработка
# Установка для разработки:

bash
git clone https://github.com/yourusername/habit-gamification-bot.git
cd habit-gamification-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install

# Code style:

bash
# Проверка code style
flake8 app tests

# Форматирование кода
black app tests

# Сортировка импортов
isort app tests

# Автор
Евдокименко Дарья - dashulyaevdokimenko@gmail.com

