import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Settings:
    """
    Класс настроек
    """

    @property
    def BOT_TOKEN(self) -> str:
        token = os.getenv("BOT_TOKEN")
        if not token:
            raise ValueError("BOT_TOKEN не найден в переменных окружения")
        return token

    @property
    def DATABASE_URL(self) -> str:
        return os.getenv("DATABASE_URL", "sqlite:///./habit_bot.db")

    @property
    def DEBUG(self) -> bool:
        return os.getenv("DEBUG", "False").lower() == "true"

    @property
    def LOG_LEVEL(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO")


# Создание экземпляра настроек
settings = Settings()