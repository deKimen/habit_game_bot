from datetime import datetime, date
from typing import Dict, Any, List, Optional
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import json

from app.db.database import Base


class DailyStats(Base):
    """
    Ежедневная статистика пользователя
    """
    __tablename__ = "daily_stats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    
    # Дата статистики
    stat_date: Mapped[date] = mapped_column(DateTime)
    
    # Основные метрики
    habits_completed: Mapped[int] = mapped_column(Integer, default=0)
    total_xp_gained: Mapped[int] = mapped_column(Integer, default=0)
    streaks_maintained: Mapped[int] = mapped_column(Integer, default=0)
    achievements_unlocked: Mapped[int] = mapped_column(Integer, default=0)
    
    # Статистика по типам привычек
    strength_habits: Mapped[int] = mapped_column(Integer, default=0)
    agility_habits: Mapped[int] = mapped_column(Integer, default=0)
    intelligence_habits: Mapped[int] = mapped_column(Integer, default=0)
    charisma_habits: Mapped[int] = mapped_column(Integer, default=0)
    
    # Системные поля
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связи
    user: Mapped["User"] = relationship("User", back_populates="daily_stats")
    
    @property
    def completion_rate(self) -> float:
        """
        Процент выполнения привычек
        """
        # Для простоты считаем что у пользователя в среднем 5 привычек
        total_possible = 5
        return (self.habits_completed / total_possible * 100) if total_possible > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Конвертирует в словарь
        """
        return {
            "date": self.stat_date.strftime("%Y-%m-%d"),
            "habits_completed": self.habits_completed,
            "total_xp_gained": self.total_xp_gained,
            "streaks_maintained": self.streaks_maintained,
            "achievements_unlocked": self.achievements_unlocked,
            "completion_rate": self.completion_rate,
            "stat_distribution": {
                "strength": self.strength_habits,
                "agility": self.agility_habits,
                "intelligence": self.intelligence_habits,
                "charisma": self.charisma_habits
            }
        }
    
    def __repr__(self) -> str:
        return f"DailyStats(user_id={self.user_id}, date={self.stat_date}, completed={self.habits_completed})"