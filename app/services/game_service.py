from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.character import Character, StatType
from app.models.habit import Habit


class GameService:
    """Сервис игровой логики"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def complete_habit(self, habit: Habit) -> Dict[str, Any]:
        """
        Обрабатывает выполнение привычки и выдает награды
        """
        # Получаем персонажа пользователя
        character = self.db.query(Character).filter(Character.user_id == habit.user_id).first()
        if not character:
            raise ValueError("Персонаж не найден")
        
        # Отмечаем привычку выполненной
        rewards = habit.mark_completed()
        
        # Начисляем награды персонажу
        total_xp = rewards["xp"] + rewards["streak_bonus"]
        leveled_up = character.add_experience(total_xp)
        
        # Увеличиваем характеристику
        character.increase_stat(rewards["stat_bonus"])
        
        # Сохраняем изменения
        self.db.commit()
        
        return {
            "character": character,
            "habit": habit,
            "xp_gained": total_xp,
            "stat_increased": rewards["stat_bonus"],
            "leveled_up": leveled_up,
            "new_level": character.level if leveled_up else None,
            "current_streak": habit.current_streak,
            "is_new_best_streak": rewards["new_best_streak"]
        }
    
    def get_character_stats(self, character: Character) -> str:
        """Форматирует статистику персонажа в красивый текст"""
        return (
            f"🎮 **Твой персонаж**\n\n"
            f"📊 Уровень: {character.level}\n"
            f"⭐ Опыт: {character.experience}/{character.experience_to_next_level}\n\n"
            f"💪 Сила: {character.strength}\n"
            f"🎯 Ловкость: {character.agility}\n" 
            f"📚 Интеллект: {character.intelligence}\n"
            f"🎭 Харизма: {character.charisma}\n\n"
            f"🔮 Всего характеристик: {character.total_stats}"
        )
    
    def get_level_up_message(self, character: Character, increased_stat: StatType) -> str:
        """Сообщение о повышении уровня"""
        stat_emoji = character.get_stat_emoji(increased_stat)
        return (
            f"🎉 **ПОЗДРАВЛЯЮ! Ты достиг {character.level} уровня!** 🎉\n\n"
            f"{stat_emoji} Твоя характеристика **{increased_stat.value}** увеличилась!\n"
            f"Продолжай в том же духе! 💫"
        )