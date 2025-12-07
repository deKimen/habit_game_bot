import asyncio
from typing import List, Optional, Dict
from datetime import time
from sqlalchemy.orm import Session
import logging
from app.models.reminder import Reminder, ReminderFrequency
from app.models.habit import Habit
from app.models.user import User

logger = logging.getLogger(__name__)


class ReminderService:
    """
    Сервис для работы с напоминаниями
    """

    def __init__(self, db: Session):
        self.db = db

    def create_reminder(
            self,
            user_id: int,
            message: str,
            reminder_time: time,
            frequency: ReminderFrequency = ReminderFrequency.DAILY,
            habit_id: Optional[int] = None,
            days: Optional[Dict[str, bool]] = None
    ) -> Reminder:

        """
        Создает новое напоминание
        """

        reminder = Reminder(
            user_id=user_id,
            message=message,
            reminder_time=reminder_time,
            frequency=frequency,
            habit_id=habit_id
        )

        # Устанавливаем дни для CUSTOM частоты
        if frequency == ReminderFrequency.CUSTOM and days:
            reminder.monday = days.get("monday", False)
            reminder.tuesday = days.get("tuesday", False)
            reminder.wednesday = days.get("wednesday", False)
            reminder.thursday = days.get("thursday", False)
            reminder.friday = days.get("friday", False)
            reminder.saturday = days.get("saturday", False)
            reminder.sunday = days.get("sunday", False)
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    def get_user_reminders(self, user_id: int, active_only: bool = True) -> List[Reminder]:
        """
        Получает напоминания пользователя
        """

        query = self.db.query(Reminder).filter(Reminder.user_id == user_id)
        if active_only:
            query = query.filter(Reminder.is_active == True)
        return query.order_by(Reminder.reminder_time).all()

    def get_reminder_by_id(self, reminder_id: int, user_id: int) -> Optional[Reminder]:
        """
        Получает напоминание по ID с проверкой владельца
        """

        return self.db.query(Reminder).filter(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id
        ).first()

    def delete_reminder(self, reminder_id: int, user_id: int) -> bool:
        """
        Удаляет напоминание
        """

        reminder = self.get_reminder_by_id(reminder_id, user_id)
        if not reminder:
            return False
        self.db.delete(reminder)
        self.db.commit()
        return True

    def toggle_reminder(self, reminder_id: int, user_id: int) -> Optional[Reminder]:
        """
        Включает/выключает напоминание
        """

        reminder = self.get_reminder_by_id(reminder_id, user_id)
        if not reminder:
            return None
        reminder.is_active = not reminder.is_active
        self.db.commit()
        return reminder

    def create_daily_motivation_reminder(self, user: User) -> Reminder:
        """
        Создает стандартное напоминание о мотивации
        """

        message = (
            "💪 Не забывай про свои привычки сегодня! "
            "Каждая выполненная привычка делает тебя сильнее! 🏆"
        )
        reminder_time = time(hour=7, minute=0)
        reminder = self.create_reminder(
            user_id=user.id,
            message=message,
            reminder_time=reminder_time,
            frequency=ReminderFrequency.DAILY
        )
        logger.info(f"Created daily motivation reminder for user {user.id}")
        return reminder

    def create_habit_reminder(self, habit: Habit, reminder_time: time) -> Reminder:
        """
        Создает напоминание для конкретной привычки
        """

        message = f"⏰ Время выполнить привычку: {habit.name}!"
        reminder = self.create_reminder(
            user_id=habit.user_id,
            message=message,
            reminder_time=reminder_time,
            frequency=ReminderFrequency.DAILY,
            habit_id=habit.id
        )
        logger.info(f"Created habit reminder for habit {habit.id}")
        return reminder

    def get_due_reminders(self) -> List[Reminder]:
        """
        Получает все напоминания, которые нужно отправить сейчас
        """

        reminders = self.db.query(Reminder).filter(Reminder.is_active == True).all()
        due_reminders = []
        for reminder in reminders:
            if reminder.is_time_to_send():
                due_reminders.append(reminder)
        return due_reminders

    def mark_reminder_sent(self, reminder: Reminder) -> None:
        """
        Отмечает напоминание как отправленное
        """

        reminder.mark_sent()
        self.db.commit()