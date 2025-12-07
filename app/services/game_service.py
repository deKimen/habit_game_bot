from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.character import Character, StatType
from app.models.habit import Habit
from app.services.achieve_service import AchievementService
from app.services.custom_service import CustomizationService


class GameService:
    """
    Сервис игровой логики
    """

    def __init__(self, db: Session):
        self.db = db
        self.achievement_service = AchievementService(db)

    def complete_habit(self, habit: Habit) -> Dict[str, Any]:
        """
        Обрабатывает выполнение привычки и выдает награды
        """
        character = self.db.query(Character).filter(Character.user_id == habit.user_id).first()
        if not character:
            raise ValueError("Персонаж не найден")
        rewards = habit.mark_completed()
        total_xp = rewards["xp"] + rewards["streak_bonus"]
        leveled_up = character.add_experience(total_xp)
        character.increase_stat(rewards["stat_bonus"])
        unlocked_achievements = self._check_achievements_after_completion(
            user_id=habit.user_id,
            habit=habit,
            character=character
        )
        unlocked_customizations = []
        if leveled_up:
            customization_service = CustomizationService(self.db)
            unlocked_customizations = customization_service.check_and_unlock_customizations(
                habit.user_id, character
            )
        self.db.commit()
        return {
            "character": character,
            "habit": habit,
            "xp_gained": total_xp,
            "stat_increased": rewards["stat_bonus"],
            "leveled_up": leveled_up,
            "new_level": character.level if leveled_up else None,
            "current_streak": habit.current_streak,
            "is_new_best_streak": rewards["new_best_streak"],
            "streak_bonus": rewards["streak_bonus"],
            "unlocked_achievements": unlocked_achievements,
            "unlocked_customizations": unlocked_customizations
        }

    def _check_achievements_after_completion(self, user_id: int, habit: Habit, character: Character) -> List[Dict]:
        """
        Проверяет все достижения после выполнения привычки
        """
        unlocked = []

        # 1. Проверяем достижения за серии
        streak_achievements = self.achievement_service.check_streak_achievements(
            user_id, habit.current_streak
        )
        unlocked.extend([{"achievement": a, "type": "streak"} for a in streak_achievements])

        # 2. Проверяем достижения за уровни
        level_achievements = self.achievement_service.check_level_achievements(
            user_id, character.level
        )
        unlocked.extend([{"achievement": a, "type": "level"} for a in level_achievements])

        # 3. Проверяем достижения за статистику
        stats = {
            StatType.STRENGTH: character.strength,
            StatType.AGILITY: character.agility,
            StatType.INTELLIGENCE: character.intelligence,
            StatType.CHARISMA: character.charisma
        }
        stat_achievements = self.achievement_service.check_stat_achievements(user_id, stats)
        unlocked.extend([{"achievement": a, "type": "stat"} for a in stat_achievements])
        return unlocked


    def get_character_stats(self, character: Character, user_id: int) -> str:
        """
        Форматирует статистику персонажа в красивый текст
        """
        achievement_service = AchievementService(self.db)
        achievement_progress = achievement_service.get_achievement_progress(user_id)
        return (
            f"🎮 **Твой персонаж**\n\n"
            f"📊 Уровень: {character.level}\n"
            f"⭐ Опыт: {character.experience}/{character.experience_to_next_level}\n\n"
            f"💪 Сила: {character.strength}\n"
            f"🎯 Ловкость: {character.agility}\n" 
            f"📚 Интеллект: {character.intelligence}\n"
            f"🎭 Харизма: {character.charisma}\n\n"
            f"🔮 Всего характеристик: {character.total_stats}"
            f"🏆 Достижения: {achievement_progress['completed']}/{achievement_progress['total']} "
            f"({achievement_progress['completion_rate']:.1f}%)"
        )

    @staticmethod
    def get_level_up_message(character: Character, increased_stat: StatType) -> str:
        """
        Сообщение о повышении уровня
        """
        stat_emoji = character.get_stat_emoji(increased_stat)
        return (
            f"🎉 **ПОЗДРАВЛЯЮ! Ты достиг {character.level} уровня!** 🎉\n\n"
            f"{stat_emoji} Твоя характеристика **{increased_stat.value}** увеличилась!\n"
            f"Продолжай в том же духе! 💫"
        )

    def get_completion_message(self, rewards: Dict[str, Any]) -> str:
        """
        Сообщение о выполнении привычки с достижениями и кастомизацией
        """
        habit = rewards["habit"]
        character = rewards["character"]
        stat_emoji = character.get_stat_emoji(rewards["stat_increased"])
        message = (
            f"✅ **Задание выполнено!**\n\n"
            f"🏆 {habit.name}\n"
            f"⭐ +{rewards['xp_gained']} опыта\n"
            f"{stat_emoji} +1 к {rewards['stat_increased'].value}\n"
            f"🔥 Серия: {rewards['current_streak']} дней\n"
        )
        if rewards.get("unlocked_customizations"):
            message += "\n🎨 **Разблокированы кастомизации:**\n"
            for custom_data in rewards["unlocked_customizations"][:2]:  # Показываем только первые 2
                customization = custom_data["customization"]
                message += f"• {customization.icon} {customization.name}\n"
        if rewards["streak_bonus"] > 0:
            message += f"🎯 Бонус за серию: +{rewards['streak_bonus']} XP\n"
        if rewards["is_new_best_streak"]:
            message += f"🏅 Новый рекорд серии!\n"
        if rewards["leveled_up"]:
            message += f"\n🎊 {self.get_level_up_message(character, rewards['stat_increased'])}"
        return message
