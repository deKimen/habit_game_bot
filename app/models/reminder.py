from enum import Enum
from typing import Optional
from sqlalchemy import Integer, String, DateTime, Enum as SQLEnum, Boolean, ForeignKey, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, time
from app.db.database import Base


class ReminderFrequency(str, Enum):
    DAILY = "daily"
    WEEKDAYS = "weekdays"
    WEEKENDS = "weekends"
    CUSTOM = "custom"


class Reminder(Base):
    """
    Модель напоминания о привычке
    """
    __tablename__ = "reminders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    habit_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("habits.id"), nullable=True)

    # Настройки напоминания
    message: Mapped[str] = mapped_column(String(500))
    reminder_time: Mapped[time] = mapped_column(Time)  # Время напоминания
    frequency: Mapped[ReminderFrequency] = mapped_column(SQLEnum(ReminderFrequency))

    # Дни недели (для CUSTOM частоты)
    monday: Mapped[bool] = mapped_column(Boolean, default=False)
    tuesday: Mapped[bool] = mapped_column(Boolean, default=False)
    wednesday: Mapped[bool] = mapped_column(Boolean, default=False)
    thursday: Mapped[bool] = mapped_column(Boolean, default=False)
    friday: Mapped[bool] = mapped_column(Boolean, default=False)
    saturday: Mapped[bool] = mapped_column(Boolean, default=False)
    sunday: Mapped[bool] = mapped_column(Boolean, default=False)

    # Системные поля
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_sent: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="reminders")
    habit: Mapped[Optional["Habit"]] = relationship("Habit")

    def should_send_today(self) -> bool:
        """
        Проверяет, нужно ли отправлять напоминание сегодня
        """
        if not self.is_active:
            return False
        today = datetime.now().weekday()
        if self.frequency == ReminderFrequency.DAILY:
            return True
        elif self.frequency == ReminderFrequency.WEEKDAYS:
            return today < 5  # Пн-Пт
        elif self.frequency == ReminderFrequency.WEEKENDS:
            return today >= 5  # Сб-Вс
        elif self.frequency == ReminderFrequency.CUSTOM:
            days_map = {
                0: self.monday,
                1: self.tuesday,
                2: self.wednesday,
                3: self.thursday,
                4: self.friday,
                5: self.saturday,
                6: self.sunday
            }
            return days_map.get(today, False)
        return False

    def is_time_to_send(self) -> bool:
        """
        Проверяет, наступило ли время отправки
        """
        if not self.should_send_today():
            return False
        now = datetime.now().time()
        reminder_time = self.reminder_time
        if now.hour == reminder_time.hour and now.minute == reminder_time.minute:
            if self.last_sent and self.last_sent.date() == datetime.now().date():
                return False
            return True
        return False

    def mark_sent(self) -> None:
        """
        Отмечает, что напоминание отправлено
        """
        self.last_sent = datetime.utcnow()

    def get_formatted_time(self) -> str:
        """
        Возвращает отформатированное время
        """
        return self.reminder_time.strftime("%H:%M")

    def __repr__(self) -> str:
        return f"Reminder(id={self.id}, time={self.reminder_time}, active={self.is_active})"