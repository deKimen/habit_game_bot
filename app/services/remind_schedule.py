import asyncio
import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.services.reminder_service import ReminderService
from app.bot.handlers import send_reminder_message

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """
    Планировщик для отправки напоминаний
    """

    def __init__(self, application):
        self.application = application
        self.is_running = False

    async def start(self):
        """
        Запускает планировщик
        """

        self.is_running = True
        logger.info("Reminder scheduler started")
        while self.is_running:
            try:
                await self._check_reminders()
                await asyncio.sleep(60)  # Проверяем каждую минуту
            except Exception as e:
                logger.error(f"Error in reminder scheduler: {e}")
                await asyncio.sleep(60)

    async def stop(self):
        """
        Останавливает планировщик
        """

        self.is_running = False
        logger.info("Reminder scheduler stopped")

    async def _check_reminders(self):
        """
        Проверяет и отправляет напоминания
        """

        db = SessionLocal()
        try:
            reminder_service = ReminderService(db)
            due_reminders = reminder_service.get_due_reminders()
            for reminder in due_reminders:
                await self._send_reminder(reminder, reminder_service)
        except Exception as e:
            logger.error(f"Error checking reminders: {e}")
        finally:
            db.close()

    async def _send_reminder(self, reminder, reminder_service):
        """
        Отправляет одно напоминание
        """

        try:
            if reminder.habit:
                message = (
                    f"⏰ **Напоминание о привычке**\n\n"
                    f"🏆 {reminder.habit.name}\n"
                    f"💡 {reminder.message}\n\n"
                    f"Используй /done {reminder.habit.id} чтобы отметить выполнение!"
                )
            else:
                message = f"🔔 **Напоминание**\n\n{reminder.message}"
            await self.application.bot.send_message(
                chat_id=reminder.user.telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            reminder_service.mark_reminder_sent(reminder)
            logger.info(f"Sent reminder {reminder.id} to user {reminder.user_id}")
        except Exception as e:
            logger.error(f"Error sending reminder {reminder.id}: {e}")