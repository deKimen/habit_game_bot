from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.customization import (
    Customization, CustomizationType, UserCustomization, DEFAULT_CUSTOMIZATIONS
)
from app.models.character import Character


class CustomizationService:
    """
    Сервис для работы с кастомизацией
    """

    def __init__(self, db: Session):
        self.db = db

    def initialize_default_customizations(self) -> List[Customization]:
        """
        Инициализирует стандартные элементы кастомизации в базе
        """
        # Проверяем, есть ли уже кастомизации
        existing = self.db.query(Customization).count()
        if existing > 0:
            return self.db.query(Customization).all()
        customizations = []
        for custom_data in DEFAULT_CUSTOMIZATIONS:
            customization = Customization(
                name=custom_data["name"],
                description=custom_data["description"],
                customization_type=CustomizationType(custom_data["type"]),
                icon=custom_data["icon"],
                unlock_level=custom_data["level"]
            )
            customizations.append(customization)
            self.db.add(customization)
        self.db.commit()
        return customizations

    def initialize_user_customizations(self, user_id: int) -> List[UserCustomization]:
        """
        Инициализирует кастомизации для пользователя
        """
        self.initialize_default_customizations()
        all_customizations = self.db.query(Customization).all()
        user_customizations = []
        for customization in all_customizations:
            is_unlocked = customization.unlock_level == 1
            user_custom = UserCustomization(
                user_id=user_id,
                customization_id=customization.id,
                is_unlocked=is_unlocked,
                is_active=is_unlocked
            )
            user_customizations.append(user_custom)
            self.db.add(user_custom)
        self.db.commit()
        return user_customizations

    def get_available_customizations(self, user_id: int,
                                     customization_type: Optional[CustomizationType] = None) -> List[Dict[str, Any]]:
        """
        Получает доступные кастомизации для пользователя
        """
        query = self.db.query(UserCustomization, Customization).join(Customization).filter(
            UserCustomization.user_id == user_id
        )
        if customization_type:
            query = query.filter(Customization.customization_type == customization_type)
        results = query.all()
        available = []
        for user_custom, customization in results:
            available.append({
                "id": customization.id,
                "name": customization.name,
                "description": customization.description,
                "type": customization.customization_type,
                "icon": customization.icon,
                "is_unlocked": user_custom.is_unlocked,
                "is_active": user_custom.is_active,
                "user_customization_id": user_custom.id
            })
        return available

    def unlock_customization(self, user_id: int, customization_id: int) -> Optional[Dict[str, Any]]:
        """
        Разблокирует кастомизацию для пользователя
        """
        user_custom = self.db.query(UserCustomization).filter(
            UserCustomization.user_id == user_id,
            UserCustomization.customization_id == customization_id
        ).first()
        if not user_custom or user_custom.is_unlocked:
            return None
        customization = self.db.query(Customization).filter(
            Customization.id == customization_id
        ).first()
        if not customization:
            return None
        character = self.db.query(Character).filter(Character.user_id == user_id).first()
        if not character or character.level < customization.unlock_level:
            return None
        user_custom.is_unlocked = True
        user_custom.unlocked_at = datetime.utcnow()
        self.db.commit()
        return {
            "customization": customization,
            "user_customization": user_custom
        }

    def activate_customization(self, user_id: int, customization_id: int) -> bool:
        """
        Активирует кастомизацию для пользователя
        """
        customization = self.db.query(Customization).filter(
            Customization.id == customization_id
        ).first()
        if not customization:
            return False
        same_type_customs = self.db.query(UserCustomization).join(Customization).filter(
            UserCustomization.user_id == user_id,
            Customization.customization_type == customization.customization_type,
            UserCustomization.is_unlocked == True
        ).all()
        for custom in same_type_customs:
            custom.is_active = False
        user_custom = self.db.query(UserCustomization).filter(
            UserCustomization.user_id == user_id,
            UserCustomization.customization_id == customization_id,
            UserCustomization.is_unlocked == True
        ).first()
        if not user_custom:
            return False
        user_custom.is_active = True
        self.db.commit()
        return True

    def get_active_customizations(self, user_id: int) -> Dict[CustomizationType, Dict[str, Any]]:
        """
        Получает активные кастомизации пользователя
        """
        active_customs = self.db.query(UserCustomization, Customization).join(Customization).filter(
            UserCustomization.user_id == user_id,
            UserCustomization.is_active == True
        ).all()
        result = {}
        for user_custom, customization in active_customs:
            result[customization.customization_type] = {
                "name": customization.name,
                "icon": customization.icon,
                "description": customization.description
            }
        return result

    def check_and_unlock_customizations(self, user_id: int, character: Character) -> List[Dict[str, Any]]:
        """
        Проверяет и разблокирует новые кастомизации по уровню
        """
        all_customs = self.db.query(Customization).all()
        unlocked = []
        for customization in all_customs:
            if character.level >= customization.unlock_level:
                result = self.unlock_customization(user_id, customization.id)
                if result:
                    unlocked.append(result)
        return unlocked