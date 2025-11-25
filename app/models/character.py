from enum import Enum
from typing import Optional
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import random

from app.db.database import Base


class StatType(str, Enum):
    STRENGTH = "strength"
    AGILITY = "agility" 
    INTELLIGENCE = "intelligence"
    CHARISMA = "charisma"


class Character(Base):
    """
    Модель персонажа пользователя
    """
    __tablename__ = "characters"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, index=True)
    
    # Основные характеристики
    level: Mapped[int] = mapped_column(Integer, default=1)
    experience: Mapped[int] = mapped_column(Integer, default=0)
    
    # Статы персонажа
    strength: Mapped[int] = mapped_column(Integer, default=1)
    agility: Mapped[int] = mapped_column(Integer, default=1)
    intelligence: Mapped[int] = mapped_column(Integer, default=1)
    charisma: Mapped[int] = mapped_column(Integer, default=1)
    
    # Системные поля
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user: Mapped["User"] = relationship("User", back_populates="character", uselist=False)
    
    @property
    def experience_to_next_level(self) -> int:
        """
        Рассчитывает необходимый опыт для следующего уровня
        """
        return self.level * 100
    
    @property
    def total_stats(self) -> int:
        """
        Сумма всех характеристик
        """
        return self.strength + self.agility + self.intelligence + self.charisma
    
    def add_experience(self, xp: int) -> bool:
        """
        Добавляет опыт персонажу.
        Возвращает True, если был достигнут новый уровень
        """
        self.experience += xp
        leveled_up = False
        
        while self.experience >= self.experience_to_next_level:
            self.level_up()
            leveled_up = True
            
        self.updated_at = datetime.utcnow()
        return leveled_up
    
    def level_up(self) -> None:
        """
        Повышает уровень персонажа
        """
        required_xp = self.experience_to_next_level
        self.experience -= required_xp
        self.level += 1
        
        # При повышении уровня случайная характеристика увеличивается
        stats = [StatType.STRENGTH, StatType.AGILITY, StatType.INTELLIGENCE, StatType.CHARISMA]
        random_stat = random.choice(stats)
        self.increase_stat(random_stat, 1)
    
    def increase_stat(self, stat_type: StatType, amount: int = 1) -> None:
        """
        Увеличивает указанную характеристику
        """
        if stat_type == StatType.STRENGTH:
            self.strength += amount
        elif stat_type == StatType.AGILITY:
            self.agility += amount
        elif stat_type == StatType.INTELLIGENCE:
            self.intelligence += amount
        elif stat_type == StatType.CHARISMA:
            self.charisma += amount
        
        self.updated_at = datetime.utcnow()

    @staticmethod
    def get_stat_emoji( stat_type: StatType) -> str:
        """
        Возвращает emoji для характеристики
        """
        emoji_map = {
            StatType.STRENGTH: "💪",
            StatType.AGILITY: "🎯", 
            StatType.INTELLIGENCE: "📚",
            StatType.CHARISMA: "🎭"
        }
        return emoji_map.get(stat_type, "⚡")
    
    def __repr__(self) -> str:
        return f"Character(id={self.id}, level={self.level}, user_id={self.user_id})"