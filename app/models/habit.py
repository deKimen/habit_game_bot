from enum import Enum
from typing import Optional
from sqlalchemy import Integer, String, DateTime, Enum as SQLEnum, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date

from app.db.database import Base
from app.models.character import StatType


class HabitType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class Habit(Base):
    """
    Модель привычки
    """
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    # Основные поля
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    habit_type: Mapped[HabitType] = mapped_column(SQLEnum(HabitType))

    # Игровые параметры
    stat_bonus: Mapped[StatType] = mapped_column(SQLEnum(StatType))
    xp_reward: Mapped[int] = mapped_column(Integer, default=10)

    # Трекинг прогресса
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    total_completions: Mapped[int] = mapped_column(Integer, default=0)

    # Время выполнения
    last_completed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Системные поля
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="habits")

    def mark_completed(self) -> dict:
        """
        Отмечает привычку выполненной.
        Возвращает словарь с наградами
        """
        self.current_streak += 1
        self.total_completions += 1
        self.last_completed = datetime.utcnow()
        if self.current_streak > self.best_streak:
            self.best_streak = self.current_streak
        rewards = {
            "xp": self.xp_reward + self._calculate_streak_bonus(),
            "stat_bonus": self.stat_bonus,
            "streak_bonus": self._calculate_streak_bonus(),
            "current_streak": self.current_streak,
            "is_new_best_streak": self.current_streak > (self.best_streak - 1)
        }
        return rewards

    def reset_streak(self) -> None:
        """
        Сбрасывает текущую серию выполнения
        """
        self.current_streak = 0

    def _calculate_streak_bonus(self) -> int:
        """
        Рассчитывает бонус за серию выполнения
        """
        if self.current_streak >= 30:
            return 15  # Бонус за месячную серию
        elif self.current_streak >= 7:
            return 5  # Бонус за недельную серию
        return 0

    def is_due_today(self) -> bool:
        """
        Проверяет, нужно ли выполнять привычку сегодня
        """
        if not self.last_completed:
            return True
        last_completed_date = self.last_completed.date()
        today = date.today()
        if self.habit_type == HabitType.DAILY:
            return last_completed_date < today
        elif self.habit_type == HabitType.WEEKLY:
            days_passed = (today - last_completed_date).days
            return days_passed >= 7
        else:
            return True

    def __repr__(self) -> str:
        return f"Habit(id={self.id}, name='{self.name}', type={self.habit_type})"