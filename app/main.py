import sys
import os
import logging
from typing import Any
from datetime import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler,ContextTypes, MessageHandler, filters

from app.db.database import create_tables, get_db
from app.services.user_service import UserService
from app.services.game_service import GameService
from app.services.habit_service import HabitService
from app.models.habit import HabitType, StatType
from app.utils.formatters import format_habits_list, format_today_habits
from app.services.achieve_service import AchievementService
from app.utils.achieve_formatters import format_achievements_list, format_achievement_unlock
from app.utils.formatters import format_habits_list, format_today_habits
from app.services.reminder_service import ReminderService
from app.services.remind_schedule import ReminderScheduler
from app.models.reminder import ReminderFrequency
from app.services.custom_service import CustomizationService
from app.models.customization import CustomizationType, Customization
from app.utils.custom_formatters import (
    format_customizations_list,
    format_active_customizations,
    format_customization_unlock
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class HabitBot:
    """
    Основной класс бота
    """
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.reminder_scheduler = ReminderScheduler(self.application)
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """
        Настройка обработчиков команд
        """
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("newhabit", self.newhabit_command))
        self.application.add_handler(CommandHandler("habits", self.habits_command))
        self.application.add_handler(CommandHandler("today", self.today_command))
        self.application.add_handler(CommandHandler("done", self.done_command))

        # Новые команды достижений
        self.application.add_handler(CommandHandler("achievements", self.achievements_command))
        self.application.add_handler(CommandHandler("progress", self.progress_command))
        #Команды напоминаний
        self.application.add_handler(CommandHandler("reminders", self.reminders_command))
        self.application.add_handler(CommandHandler("newreminder", self.newreminder_command))
        self.application.add_handler(CommandHandler("togglereminder", self.togglereminder_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        # Команды кастомизации
        self.application.add_handler(CommandHandler("customize", self.customize_command))
        self.application.add_handler(CommandHandler("activate", self.activate_command))
        self.application.add_handler(CommandHandler("look", self.look_command))

    @staticmethod
    async def start_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /start
        """
        user = update.effective_user
        db = next(get_db())
        try:
            user_service = UserService(db)
            db_user = user_service.get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            game_service = GameService(db)
            stats_text = game_service.get_character_stats(db_user.character)
            welcome_text = (
                f"Привет, {db_user.display_name}! 👋\n\n"
                f"Добро пожаловать в **Habit Gamification Bot**! 🎮\n\n"
                f"Здесь ты можешь прокачивать своего персонажа, выполняя полезные привычки!\n\n"
                f"{stats_text}\n\n"
                f"📚 **Основные команды:**\n"
                f"/newhabit - добавить привычку\n"
                f"/habits - список всех привычек\n"
                f"/today - что сделать сегодня\n"
                f"/done - отметить выполнение\n"
                f"/stats - статистика персонажа\n"
                f"/help - помощь"
            )
            await update.message.reply_text(welcome_text, parse_mode='Markdown')
        except Exception as e:
            logger.error("Error in start command: %s", e)
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
        finally:
            db.close()

    @staticmethod
    async def stats_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /stats
        """
        user = update.effective_user
        db = next(get_db())
        try:
            user_service = UserService(db)
            db_user = user_service.get_user_with_character(user.id)
            if not db_user:
                await update.message.reply_text("Сначала используйте /start для создания персонажа")
                return
            game_service = GameService(db)
            habit_service = HabitService(db)
            customization_service = CustomizationService(db)
            character_stats_text = game_service.get_character_stats(db_user.character)
            habit_stats = habit_service.get_habit_stats(user.id)
            active_customs = customization_service.get_active_customizations(user.id)
            stats_text = (
                f"{character_stats_text}\n\n"
                f"📊 **Статистика привычек:**\n"
                f"📝 Всего привычек: {habit_stats['total_habits']}\n"
                f"🔥 Активных серий: {habit_stats['active_streaks']}\n"
                f"✅ Всего выполнений: {habit_stats['total_completions']}\n"
                f"📅 На сегодня: {habit_stats['today_habits']}"
            )
            if active_customs:
                stats_text += "\n\n🎭 **Текущий вид:**"
                for custom_type, custom_data in active_customs.items():
                    type_name = "Внешность" if custom_type == CustomizationType.SKIN else "Титул"
                    stats_text += f"\n{custom_data['icon']} {type_name}: {custom_data['name']}"
            await update.message.reply_text(stats_text, parse_mode='Markdown')
        except Exception as e:
            logger.error("Error in stats command: %s", e)
            await update.message.reply_text("❌ Произошла ошибка при получении статистики")
        finally:
            db.close()

    @staticmethod
    async def newhabit_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /newhabit
        """
        user = update.effective_user
        db = next(get_db())
        try:
            user_service = UserService(db)
            db_user = user_service.get_user_with_character(user.id)
            if not db_user:
                await update.message.reply_text("Сначала используйте /start для создания персонажа")
                return
            if not context.args:
                help_text = (
                    "📝 **Добавление новой привычки**\n\n"
                    "Используй: /newhabit <название> <тип> <характеристика>\n\n"
                    "**Типы привычек:**\n"
                    "• daily - ежедневная\n"
                    "• weekly - еженедельная\n"
                    "• custom - произвольная\n\n"
                    "**Характеристики:**\n"
                    "• strength - 💪 Сила\n"
                    "• agility - 🎯 Ловкость\n"
                    "• intelligence - 📚 Интеллект\n"
                    "• charisma - 🎭 Харизма\n\n"
                    "**Пример:**\n"
                    "`/newhabit Утренняя_зарядка daily strength`"
                )
                await update.message.reply_text(help_text, parse_mode='Markdown')
                return
            if len(context.args) < 3:
                await update.message.reply_text("❌ Недостаточно аргументов. Используй /newhabit для справки.")
                return
            name = context.args[0].replace('_', ' ')
            habit_type_str = context.args[1].lower()
            stat_str = context.args[2].lower()
            try:
                habit_type = HabitType(habit_type_str)
            except ValueError:
                await update.message.reply_text("❌ Неверный тип привычки. Используй: daily, weekly или custom")
                return
            try:
                stat_bonus = StatType(stat_str)
            except ValueError:
                await update.message.reply_text(
                    "❌ Неверная характеристика. Используй: strength, agility, intelligence или charisma")
                return
            habit_service = HabitService(db)
            habit = habit_service.create_habit(
                user_id=db_user.id,
                name=name,
                habit_type=habit_type,
                stat_bonus=stat_bonus
            )
            stat_emoji = db_user.character.get_stat_emoji(stat_bonus)
            success_text = (
                f"✅ **Привычка добавлена!**\n\n"
                f"🏆 **{habit.name}**\n"
                f"📅 Тип: {habit.habit_type.value}\n"
                f"{stat_emoji} Прокачка: {habit.stat_bonus.value}\n"
                f"⭐ Награда: {habit.xp_reward} XP\n"
                f"🔢 ID: {habit.id}\n\n"
                f"💡 Используй /done {habit.id} чтобы отметить выполнение!"
            )
            await update.message.reply_text(success_text, parse_mode='Markdown')
        except Exception as e:
            logger.error("Error in newhabit command: %s", e)
            await update.message.reply_text("❌ Произошла ошибка при создании привычки")
        finally:
            db.close()

    @staticmethod
    async def habits_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /habits
        """
        user = update.effective_user
        db = next(get_db())
        try:
            user_service = UserService(db)
            db_user = user_service.get_user_with_character(user.id)
            if not db_user:
                await update.message.reply_text("Сначала используйте /start для создания персонажа")
                return
            habit_service = HabitService(db)
            habits = habit_service.get_user_habits(user.id)
            habits_text = format_habits_list(habits)
            await update.message.reply_text(habits_text, parse_mode='Markdown')
        except Exception as e:
            logger.error("Error in habits command: %s", e)
            await update.message.reply_text("❌ Произошла ошибка при получении списка привычек")
        finally:
            db.close()

    @staticmethod
    async def today_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /today
        """
        user = update.effective_user
        db = next(get_db())
        try:
            user_service = UserService(db)
            db_user = user_service.get_user_with_character(user.id)
            if not db_user:
                await update.message.reply_text("Сначала используйте /start для создания персонажа")
                return
            habit_service = HabitService(db)
            today_habits = habit_service.get_today_habits(user.id)
            today_text = format_today_habits(today_habits)
            await update.message.reply_text(today_text, parse_mode='Markdown')
        except Exception as e:
            logger.error("Error in today command: %s", e)
            await update.message.reply_text("❌ Произошла ошибка при получении списка на сегодня")
        finally:
            db.close()

    @staticmethod
    async def done_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /done
        """
        user = update.effective_user
        db = next(get_db())
        try:
            if not context.args:
                await update.message.reply_text("❌ Укажи ID привычки. Пример: /done 1")
                return
            try:
                habit_id = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ ID привычки должен быть числом. Пример: /done 1")
                return
            user_service = UserService(db)
            db_user = user_service.get_user_with_character(user.id)
            if not db_user:
                await update.message.reply_text("Сначала используйте /start для создания персонажа")
                return
            habit_service = HabitService(db)
            habit = habit_service.get_habit_by_id(habit_id, db_user.id)
            if not habit:
                await update.message.reply_text("❌ Привычка не найдена. Проверь ID через /habits")
                return
            if not habit.is_active:
                await update.message.reply_text("❌ Эта привычка удалена")
                return
            if not habit.is_due_today():
                await update.message.reply_text("⏳ Эту привычку не нужно выполнять сегодня")
                return
            game_service = GameService(db)
            rewards = game_service.complete_habit(habit)
            completion_text = game_service.get_completion_message(rewards)
            await update.message.reply_text(completion_text, parse_mode='Markdown')
        except Exception as e:
            logger.error("Error in done command: %s", e)
            await update.message.reply_text("❌ Произошла ошибка при отметке выполнения")
        finally:
            db.close()

    @staticmethod
    async def help_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /help
        """
        help_text = (
            "🎮 **Habit Gamification Bot - Помощь**\n\n"
            "Доступные команды:\n\n"
            "🔹 /start - Начать работу, создать персонажа\n"
            "🔹 /stats - Посмотреть статистику персонажа\n"
            "🔹 /help - Показать это сообщение\n\n"
            "📚 **Как это работает:**\n"
            "1. Создаешь привычки (скоро будет!)\n"
            "2. Выполняешь их в реальной жизни\n"
            "3. Отмечаешь выполнение в боте\n"
            "4. Получаешь опыт и прокачиваешь персонажа!\n\n"
            "💪 Сила - спорт, зарядка\n"
            "🎯 Ловкость - навыки, координация\n"
            "📚 Интеллект - учёба, чтение\n"
            "🎭 Харизма - общение, творчество"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')

    @staticmethod
    async def achievements_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /achievements
        """
        user = update.effective_user
        db = next(get_db())
        try:
            user_service = UserService(db)
            db_user = user_service.get_user_with_character(user.id)
            if not db_user:
                await update.message.reply_text("Сначала используйте /start для создания персонажа")
                return
            achievement_service = AchievementService(db)
            achievements = achievement_service.get_user_achievements(user.id)
            achievements_text = format_achievements_list(achievements)
            await update.message.reply_text(achievements_text, parse_mode='Markdown')
        except Exception as e:
            logger.error("Error in achievements command: %s", e)
            await update.message.reply_text("❌ Произошла ошибка при получении достижений")
        finally:
            db.close()

    @staticmethod
    async def progress_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /progress
        """
        user = update.effective_user
        db = next(get_db())
        try:
            user_service = UserService(db)
            db_user = user_service.get_user_with_character(user.id)
            if not db_user:
                await update.message.reply_text("Сначала используйте /start для создания персонажа")
                return
            achievement_service = AchievementService(db)
            progress = achievement_service.get_achievement_progress(user.id)
            progress_text = (
                f"📊 **Прогресс по достижениям:**\n\n"
                f"🎯 Всего достижений: {progress['total']}\n"
                f"✅ Получено: {progress['completed']}\n"
                f"⏳ В процессе: {progress['in_progress']}\n"
                f"📈 Завершено: {progress['completion_rate']:.1f}%\n\n"
                f"💡 Используй /achievements чтобы увидеть список"
            )
            await update.message.reply_text(progress_text, parse_mode='Markdown')
        except Exception as e:
            logger.error("Error in progress command: %s", e)
            await update.message.reply_text("❌ Произошла ошибка при получении прогресса")
        finally:
            db.close()

    @staticmethod
    async def customize_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /customize
        """
        user = update.effective_user
        db = next(get_db())
        try:
            user_service = UserService(db)
            db_user = user_service.get_user_with_character(user.id)
            if not db_user:
                await update.message.reply_text("Сначала используйте /start для создания персонажа")
                return
            customization_service = CustomizationService(db)
            if context.args:
                try:
                    custom_type = CustomizationType(context.args[0].lower())
                    customizations = customization_service.get_available_customizations(
                        db_user.id, custom_type
                    )
                    if not customizations:
                        await update.message.reply_text("❌ Кастомизации этого типа не найдены")
                        return
                    custom_text = format_customizations_list(customizations, custom_type)
                    await update.message.reply_text(custom_text, parse_mode='Markdown')
                    return
                except ValueError:
                    pass
            help_text = (
                "🎨 **Кастомизация персонажа**\n\n"
                "Измени внешний вид своего персонажа!\n\n"
                "**Типы кастомизации:**\n"
                "• skin - скины/внешность персонажа\n"
                "• title - титулы и звания\n"
                "• badge - значки и достижения\n\n"
                "**Команды:**\n"
                "• /customize skin - показать скины\n"
                "• /customize title - показать титулы\n"
                "• /customize badge - показать значки\n"
                "• /activate <ID> - активировать кастомизацию\n"
                "• /look - посмотреть текущий вид\n\n"
                "**Пример:** `/customize skin`"
            )
            await update.message.reply_text(help_text, parse_mode='Markdown')
        except Exception as e:
            logger.error("Error in customize command: %s", e)
            await update.message.reply_text("❌ Произошла ошибка")
        finally:
            db.close()

    @staticmethod
    async def activate_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /activate
        """
        user = update.effective_user
        db = next(get_db())
        try:
            if not context.args:
                await update.message.reply_text("❌ Укажи ID кастомизации. Пример: /activate 1")
                return
            try:
                customization_id = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ ID должен быть числом")
                return
            user_service = UserService(db)
            db_user = user_service.get_user_with_character(user.id)
            if not db_user:
                await update.message.reply_text("Сначала используйте /start для создания персонажа")
                return
            customization_service = CustomizationService(db)
            success = customization_service.activate_customization(db_user.id, customization_id)
            if not success:
                await update.message.reply_text(
                    "❌ Не удалось активировать кастомизацию.\n"
                    "Возможно, она не разблокирована или не существует."
                )
                return
            customization = db.query(Customization).filter(Customization.id == customization_id).first()
            if customization:
                success_text = (
                    f"✅ **Кастомизация активирована!**\n\n"
                    f"{customization.icon} **{customization.name}**\n"
                    f"📝 {customization.description}\n\n"
                    f"🎨 Твой персонаж теперь выглядит по-новому!"
                )
                await update.message.reply_text(success_text, parse_mode='Markdown')
            else:
                await update.message.reply_text("✅ Кастомизация активирована!")
        except Exception as e:
            logger.error("Error in activate command: %s", e)
            await update.message.reply_text("❌ Произошла ошибка")
        finally:
            db.close()

    @staticmethod
    async def look_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /look
        """
        user = update.effective_user
        db = next(get_db())
        try:
            user_service = UserService(db)
            db_user = user_service.get_user_with_character(user.id)
            if not db_user:
                await update.message.reply_text("Сначала используйте /start для создания персонажа")
                return
            customization_service = CustomizationService(db)
            active_customs = customization_service.get_active_customizations(db_user.id)
            look_text = format_active_customizations(active_customs)
            await update.message.reply_text(look_text, parse_mode='Markdown')
        except Exception as e:
            logger.error("Error in look command: %s", e)
            await update.message.reply_text("❌ Произошла ошибка")
        finally:
            db.close()

    @staticmethod
    async def handle_message(update: Update, context: Any) -> None:
        """
        Обработчик текстовых сообщений
        """
        message_text = (
            "🤖 Я бот для трекинга привычек!\n\n"
            "Используй команды:\n"
            "/start - начать работу\n"
            "/newhabit - добавить привычку\n"
            "/habits - мои привычки\n"
            "/today - что сделать сегодня\n"
            "/done - отметить выполнение\n"
            "/stats - статистика\n"
            "/help - помощь"
        )
        await update.message.reply_text(message_text)

    @staticmethod
    async def reminders_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /reminders
        """
        user = update.effective_user
        db = next(get_db())
        try:
            user_service = UserService(db)
            db_user = user_service.get_user_with_character(user.id)
            if not db_user:
                await update.message.reply_text("Сначала используйте /start для создания персонажа")
                return
            reminder_service = ReminderService(db)
            user_reminders = reminder_service.get_user_reminders(db_user.id)
            if not user_reminders:
                help_text = (
                    "🔔 **Управление напоминаниями**\n\n"
                    "У тебя пока нет напоминаний.\n\n"
                    "**Доступные команды:**\n"
                    "• /newreminder - создать новое напоминание\n"
                    "• /remindhabit - напоминание для привычки\n"
                    "• /togglereminder - вкл/выкл напоминание\n"
                    "• /deletereminder - удалить напоминание"
                )
                await update.message.reply_text(help_text, parse_mode='Markdown')
                return
            lines = ["🔔 **Твои напоминания:**\n"]
            for reminder in user_reminders:
                status_emoji = "✅" if reminder.is_active else "❌"
                time_str = reminder.get_formatted_time()
                habit_info = f" для '{reminder.habit.name}'" if reminder.habit else ""
                lines.append(
                    f"{status_emoji} **{time_str}**{habit_info}\n"
                    f"   📝 {reminder.message}\n"
                    f"   📅 {reminder.frequency.value} | ID: {reminder.id}"
                )
            lines.append("\n💡 Используй /togglereminder <ID> для включения/выключения")
            await update.message.reply_text("\n".join(lines), parse_mode='Markdown')
        except Exception as e:
            logger.error("Error in reminders command: %s", e)
            await update.message.reply_text("❌ Произошла ошибка при получении напоминаний")
        finally:
            db.close()

    @staticmethod
    async def newreminder_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /newreminder
        """
        user = update.effective_user
        db = next(get_db())
        try:
            user_service = UserService(db)
            db_user = user_service.get_user_with_character(user.id)
            if not db_user:
                await update.message.reply_text("Сначала используйте /start для создания персонажа")
                return
            if len(context.args) < 2:
                help_text = (
                    "⏰ **Создание напоминания**\n\n"
                    "Используй: /newreminder <время> <сообщение>\n\n"
                    "**Время в формате:** HH:MM\n"
                    "**Примеры:**\n"
                    "`/newreminder 09:00 Доброе утро! Пора выполнять привычки!`\n"
                    "`/newreminder 20:00 Подведи итоги дня`\n\n"
                    "💡 Напоминания будут приходить ежедневно."
                )
                await update.message.reply_text(help_text, parse_mode='Markdown')
                return
            try:
                time_str = context.args[0]
                hours, minutes = map(int, time_str.split(':'))
                if not (0 <= hours < 24 and 0 <= minutes < 60):
                    raise ValueError
                reminder_time = time(hour=hours, minute=minutes)
            except (ValueError, IndexError):
                await update.message.reply_text("❌ Неверный формат времени. Используй HH:MM")
                return
            message = ' '.join(context.args[1:])
            reminder_service = ReminderService(db)
            reminder = reminder_service.create_reminder(
                user_id=db_user.id,
                message=message,
                reminder_time=reminder_time,
                frequency=ReminderFrequency.DAILY
            )
            success_text = (
                f"✅ **Напоминание создано!**\n\n"
                f"⏰ Время: {reminder.get_formatted_time()}\n"
                f"📝 Сообщение: {reminder.message}\n"
                f"📅 Частота: ежедневно\n"
                f"🔢 ID: {reminder.id}\n\n"
                f"💡 Используй /togglereminder {reminder.id} чтобы включить/выключить"
            )
            await update.message.reply_text(success_text, parse_mode='Markdown')
        except Exception as e:
            logger.error("Error in newreminder command: %s", e)
            await update.message.reply_text("❌ Произошла ошибка при создании напоминания")
        finally:
            db.close()

    @staticmethod
    async def togglereminder_command(update: Update, context: Any) -> None:
        """
        Обработчик команды /togglereminder
        """
        user = update.effective_user
        db = next(get_db())
        try:
            if not context.args:
                await update.message.reply_text("❌ Укажи ID напоминания. Пример: /togglereminder 1")
                return
            try:
                reminder_id = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ ID должен быть числом")
                return
            user_service = UserService(db)
            db_user = user_service.get_user_with_character(user.id)
            if not db_user:
                await update.message.reply_text("Сначала используйте /start для создания персонажа")
                return
            reminder_service = ReminderService(db)
            reminder = reminder_service.toggle_reminder(reminder_id, db_user.id)
            if not reminder:
                await update.message.reply_text("❌ Напоминание не найдено")
                return
            status = "включено" if reminder.is_active else "выключено"
            await update.message.reply_text(f"✅ Напоминание {status}!")
        except Exception as e:
            logger.error("Error in togglereminder command: %s", e)
            await update.message.reply_text("❌ Произошла ошибка")
        finally:
            db.close()

    def run(self) -> None:
        """
        Запуск бота
        """
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Создаем задачу для планировщика
        scheduler_task = loop.create_task(self.reminder_scheduler.start())
        try:
            self.application.run_polling()
        except KeyboardInterrupt:
            print("\n🛑 Останавливаем бота...")
        finally:
            loop.run_until_complete(self.reminder_scheduler.stop())
            scheduler_task.cancel()
            loop.close()

def main() -> None:
    """
    Основная функция
    """
    # Создание таблиц БД
    create_tables()
    # Получение токена бота
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")
    # Запуск бота
    bot = HabitBot(bot_token)
    print("🤖 Бот запущен...")
    bot.run()

if __name__ == "__main__":
    main()