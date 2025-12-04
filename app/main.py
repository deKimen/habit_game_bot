import sys
import os
import logging
from typing import Any
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler,ContextTypes, MessageHandler, filters

from app.db.database import create_tables, get_db
from app.services.user_service import UserService
from app.services.game_service import GameService
from app.services.habit_service import HabitService
from app.models.habit import HabitType, StatType
from app.utils.formatters import format_habits_list, format_today_habits
from app.services.achievement_service import AchievementService
from app.utils.achievement_formatters import format_achievements_list, format_achievement_unlock
from app.utils.formatters import format_habits_list, format_today_habits

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

        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

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
            character_stats_text = game_service.get_character_stats(db_user.character)
            habit_stats = habit_service.get_habit_stats(user.id)
            stats_text = (
                f"{character_stats_text}\n\n"
                f"📊 **Статистика привычек:**\n"
                f"📝 Всего привычек: {habit_stats['total_habits']}\n"
                f"🔥 Активных серий: {habit_stats['active_streaks']}\n"
                f"✅ Всего выполнений: {habit_stats['total_completions']}\n"
                f"📅 На сегодня: {habit_stats['today_habits']}"
            )
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

    def run(self) -> None:
        """
        Запуск бота
        """
        self.application.run_polling()

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