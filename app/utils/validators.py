"""Валидаторы для данных"""
from typing import Any


def validate_habit_name(name: str) -> bool:
    """Проверяет валидность названия привычки"""
    if not name or len(name.strip()) == 0:
        return False
    if len(name) > 255:
        return False
    return True


def validate_xp_value(xp: int) -> bool:
    """Проверяет валидность значения опыта"""
    return 0 <= xp <= 1000