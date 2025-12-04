from enum import Enum
from typing import Optional
from sqlalchemy import Integer, String, DateTime, Enum as SQLEnum, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.database import Base


class CustomizationType(str, Enum):
    SKIN = "skin"  # Внешний вид персонажа
    TITLE = "title"  # Титул/звание
    BADGE = "badge"  # Значок
    COLOR = "color"  # Цвет
    ANIMATION = "animation"  # Анимация


class Customization(Base):
    """
    Модель элемента кастомизации
    """
    __tablename__ = "customizations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255))
    customization_type: Mapped[CustomizationType] = mapped_column(SQLEnum(CustomizationType))
    icon: Mapped[str] = mapped_column(String(50))  # Emoji или код иконки
    unlock_level: Mapped[int] = mapped_column(Integer, default=1)
    unlock_achievement_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"Customization(id={self.id}, name='{self.name}', type={self.customization_type})"


class UserCustomization(Base):
    """
    Связь пользователя с элементами кастомизации
    """

    __tablename__ = "user_customizations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    customization_id: Mapped[int] = mapped_column(Integer, ForeignKey("customizations.id"))
    is_unlocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    unlocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship("User", back_populates="customizations")
    customization: Mapped["Customization"] = relationship("Customization")

    def __repr__(self) -> str:
        return f"UserCustomization(user_id={self.user_id}, customization_id={self.customization_id})"

DEFAULT_CUSTOMIZATIONS = [
    # Скины по умолчанию
    {"name": "Новичок", "description": "Стандартный вид персонажа", "type": CustomizationType.SKIN, "icon": "👤",
     "level": 1},
    {"name": "Воин", "description": "Для сильных духом", "type": CustomizationType.SKIN, "icon": "⚔️", "level": 5},
    {"name": "Маг", "description": "Для мудрых и интеллектуальных", "type": CustomizationType.SKIN, "icon": "🔮",
     "level": 10},
    {"name": "Ловкач", "description": "Для быстрых и ловких", "type": CustomizationType.SKIN, "icon": "🏹", "level": 15},

    # Титулы
    {"name": "Новичок", "description": "Только начал свой путь", "type": CustomizationType.TITLE, "icon": "🌱",
     "level": 1},
    {"name": "Ученик", "description": "Делает первые успехи", "type": CustomizationType.TITLE, "icon": "📚", "level": 3},
    {"name": "Мастер", "description": "Достиг высокого уровня", "type": CustomizationType.TITLE, "icon": "👑",
     "level": 20},
    {"name": "Легенда", "description": "Невероятные достижения", "type": CustomizationType.TITLE, "icon": "🌟",
     "level": 30},

    # Значки
    {"name": "Первые шаги", "description": "Первая выполненная привычка", "type": CustomizationType.BADGE, "icon": "🥇",
     "level": 1},
    {"name": "Неделя силы", "description": "7 дней подряд", "type": CustomizationType.BADGE, "icon": "🔥", "level": 7},
    {"name": "Месяц дисциплины", "description": "30 дней подряд", "type": CustomizationType.BADGE, "icon": "📅",
     "level": 30},
]