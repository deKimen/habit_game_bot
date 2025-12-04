from enum import Enum
from typing import Optional
from sqlalchemy import Integer, String, DateTime, Enum as SQLEnum, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.database import Base


class AchievementType(str, Enum):
    STREAK = "streak"  # за серии
    LEVEL = "level"  # за уровни
    HABIT_COUNT = "habit_count"  # за количество привычек
    COMPLETION = "completion"  # за выполнение
    STAT = "stat"  # за характеристики


class Achievement(Base):
    """
    Модель достижения
    """
    __tablename__ = "achievements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    # Основные поля
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String)
    achievement_type: Mapped[AchievementType] = mapped_column(SQLEnum(AchievementType))

    # Условия получения
    condition_value: Mapped[int] = mapped_column(Integer)  # например, 7 дней серии
    reward_xp: Mapped[int] = mapped_column(Integer, default=50)

    # Прогресс
    progress: Mapped[int] = mapped_column(Integer, default=0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Системные поля
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="achievements")

    def update_progress(self, new_progress: int) -> bool:
        """
        Обновляет прогресс достижения.
        Возвращает True, если достижение завершено
        """
        if self.is_completed:
            return False
        self.progress = max(self.progress, new_progress)
        if self.progress >= self.condition_value and not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
            return True
        return False

    def __repr__(self) -> str:
        return f"Achievement(id={self.id}, name='{self.name}', completed={self.is_completed})"

DEFAULT_ACHIEVEMENTS = [
    # Серии
    {"name": "🔥 Первая серия", "description": "Выполняй привычку 3 дня подряд", "type": AchievementType.STREAK,
     "condition": 3, "xp": 25},
    {"name": "🔥 Неделя силы воли", "description": "7 дней подряд выполнения привычек", "type": AchievementType.STREAK,
     "condition": 7, "xp": 50},
    {"name": "🔥 Месяц дисциплины", "description": "30 дней подряд выполнения привычек", "type": AchievementType.STREAK,
     "condition": 30, "xp": 100},

    # Уровни
    {"name": "⭐ Новичок", "description": "Достигни 5 уровня", "type": AchievementType.LEVEL, "condition": 5, "xp": 50},
    {"name": "⭐ Опытный", "description": "Достигни 10 уровня", "type": AchievementType.LEVEL, "condition": 10,
     "xp": 100},
    {"name": "⭐ Мастер", "description": "Достигни 20 уровня", "type": AchievementType.LEVEL, "condition": 20,
     "xp": 200},

    # Привычки
    {"name": "📝 Коллекционер", "description": "Создай 5 привычек", "type": AchievementType.HABIT_COUNT, "condition": 5,
     "xp": 50},
    {"name": "📝 Энтузиаст", "description": "Создай 10 привычек", "type": AchievementType.HABIT_COUNT, "condition": 10,
     "xp": 100},

    # Выполнения
    {"name": "✅ Первые шаги", "description": "Выполни 10 привычек", "type": AchievementType.COMPLETION, "condition": 10,
     "xp": 25},
    {"name": "✅ Трудолюбивый", "description": "Выполни 50 привычек", "type": AchievementType.COMPLETION,
     "condition": 50, "xp": 75},
    {"name": "✅ Легенда", "description": "Выполни 100 привычек", "type": AchievementType.COMPLETION, "condition": 100,
     "xp": 150},

    # Характеристики
    {"name": "💪 Качок", "description": "Достигни 10 силы", "type": AchievementType.STAT, "condition": 10, "xp": 100},
    {"name": "📚 Умный человек в очках", "description": "Достигни 10 интеллекта", "type": AchievementType.STAT, "condition": 10,
     "xp": 100},
]