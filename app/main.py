import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.db.database import create_tables, get_db
from app.services.user_service import UserService
from app.services.game_service import GameService

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class HabitBot:
    """Основной класс бота"""
    
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
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
                f"Используй команды:\n"
                f"/stats - посмотреть статистику\n"
                f"/help - получить помощь"
            )
            
            await update.message.reply_text(welcome_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /stats"""
        user = update.effective_user
        db = next(get_db())
        
        try:
            user_service = UserService(db)
            db_user = user_service.get_user_with_character(user.id)
            
            if not db_user:
                await update.message.reply_text("Сначала используйте /start для создания персонажа")
                return
            
            game_service = GameService(db)
            stats_text = game_service.get_character_stats(db_user.character)
            
            await update.message.reply_text(stats_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in stats command: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении статистики")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
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
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        message_text = "Я пока умею только показывать статистику! Используй /stats или /help"
        await update.message.reply_text(message_text)
    
    def run(self):
        """Запуск бота"""
        self.application.run_polling()


def main():
    """Основная функция"""
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