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
    @staticmethod
    def get_character_stats(character: Character) -> str:
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
    @staticmethod
    def get_level_up_message(character: Character, increased_stat: StatType) -> str:
        """Сообщение о повышении уровня"""
        stat_emoji = character.get_stat_emoji(increased_stat)
        return (
            f"🎉 **ПОЗДРАВЛЯЮ! Ты достиг {character.level} уровня!** 🎉\n\n"
            f"{stat_emoji} Твоя характеристика **{increased_stat.value}** увеличилась!\n"
            f"Продолжай в том же духе! 💫"
        )

    def get_completion_message(self, rewards: Dict[str, Any]) -> str:
        """Сообщение о выполнении привычки"""
        habit = rewards["habit"]
        character = rewards["character"]
        stat_emoji = character.get_stat_emoji(rewards["stat_increased"])

        message = (
            f"✅ **Привычка выполнена!**\n\n"
            f"🏆 {habit.name}\n"
            f"⭐ +{rewards['xp_gained']} опыта\n"
            f"{stat_emoji} +1 к {rewards['stat_increased'].value}\n"
            f"🔥 Серия: {rewards['current_streak']} дней\n"
        )

        if rewards["streak_bonus"] > 0:
            message += f"🎯 Бонус за серию: +{rewards['streak_bonus']} XP\n"

        if rewards["is_new_best_streak"]:
            message += f"🏅 Новый рекорд серии!\n"

        if rewards["leveled_up"]:
            message += f"\n🎊 {self.get_level_up_message(character, rewards['stat_increased'])}"

        return message