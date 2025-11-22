from enum import Enum
from typing import Optional
from sqlalchemy import Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.database import Base
from app.models.character import StatType


class HabitType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class Habit(Base):
    """Модель привычки"""
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
    
    # Системные поля
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Связи
    user: Mapped["User"] = relationship("User", back_populates="habits")
    
    def mark_completed(self) -> dict:
        """
        Отмечает привычку выполненной
        Возвращает словарь с наградами
        """
        self.current_streak += 1
        self.total_completions += 1
        
        if self.current_streak > self.best_streak:
            self.best_streak = self.current_streak
        
        rewards = {
            "xp": self.xp_reward,
            "stat_bonus": self.stat_bonus,
            "streak_bonus": self._calculate_streak_bonus(),
            "new_best_streak": self.current_streak > self.best_streak
        }
        
        return rewards
    
    def reset_streak(self) -> None:
        """Сбрасывает текущую серию выполнения"""
        self.current_streak = 0
    
    def _calculate_streak_bonus(self) -> int:
        """Рассчитывает бонус за серию выполнения"""
        if self.current_streak >= 7:
            return 5  # Бонус за недельную серию
        elif self.current_streak >= 30:
            return 15  # Бонус за месячную серию
        return 0
    
    def __repr__(self) -> str:
        return f"Habit(id={self.id}, name='{self.name}', type={self.habit_type})"