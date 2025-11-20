from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.character import Character


class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_user(self, telegram_id: int, username: Optional[str] = None, 
                          first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        """
        Получает существующего пользователя или создает нового
        """
        user = self.get_user_by_telegram_id(telegram_id)
        
        if not user:
            user = self.create_user(telegram_id, username, first_name, last_name)
        
        return user
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получает пользователя по Telegram ID"""
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()
    
    def create_user(self, telegram_id: int, username: Optional[str] = None,
                   first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        """
        Создает нового пользователя и персонажа
        """
        # Создаем пользователя
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        self.db.add(user)
        self.db.flush()  # Получаем ID пользователя
        
        # Создаем персонажа
        character = Character(user_id=user.id)
        self.db.add(character)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def get_user_with_character(self, telegram_id: int) -> Optional[User]:
        """Получает пользователя вместе с персонажем"""
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()