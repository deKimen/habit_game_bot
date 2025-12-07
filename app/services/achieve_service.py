from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.achievements import Achievement, AchievementType, DEFAULT_ACHIEVEMENTS
from app.models.character import StatType


class AchievementService:
    """
    Сервис для работы с достижениями
    """

    def __init__(self, db: Session):
        self.db = db

    def initialize_user_achievements(self, user_id: int) -> List[Achievement]:
        """
        Инициализирует стандартные достижения для пользователя
        """
        achievements = []
        for achievement_data in DEFAULT_ACHIEVEMENTS:
            achievement = Achievement(
                user_id=user_id,
                name=achievement_data["name"],
                description=achievement_data["description"],
                achievement_type=AchievementType(achievement_data["type"]),
                condition_value=achievement_data["condition"],
                reward_xp=achievement_data["xp"]
            )
            achievements.append(achievement)
            self.db.add(achievement)
        self.db.commit()
        return achievements

    def get_user_achievements(self, user_id: int, completed_only: bool = False) -> List[Achievement]:
        """
        Получает достижения пользователя
        """
        query = self.db.query(Achievement).filter(Achievement.user_id == user_id)
        if completed_only:
            query = query.filter(Achievement.is_completed == True)
        return query.order_by(
            Achievement.is_completed.desc(),
            Achievement.achievement_type,
            Achievement.condition_value
        ).all()

    def check_streak_achievements(self, user_id: int, streak_length: int) -> List[Achievement]:
        """
        Проверяет достижения за серии
        """
        streak_achievements = self.db.query(Achievement).filter(
            Achievement.user_id == user_id,
            Achievement.achievement_type == AchievementType.STREAK,
            Achievement.is_completed == False
        ).all()
        completed = []
        for achievement in streak_achievements:
            if streak_length >= achievement.condition_value:
                if achievement.update_progress(streak_length):
                    completed.append(achievement)
        if completed:
            self.db.commit()
        return completed

    def check_level_achievements(self, user_id: int, level: int) -> List[Achievement]:
        """
        Проверяет достижения за уровни
        """
        level_achievements = self.db.query(Achievement).filter(
            Achievement.user_id == user_id,
            Achievement.achievement_type == AchievementType.LEVEL,
            Achievement.is_completed == False
        ).all()
        completed = []
        for achievement in level_achievements:
            if level >= achievement.condition_value:
                if achievement.update_progress(level):
                    completed.append(achievement)
        if completed:
            self.db.commit()
        return completed

    def check_habit_count_achievements(self, user_id: int, habit_count: int) -> List[Achievement]:
        """
        Проверяет достижения за количество привычек
        """
        habit_achievements = self.db.query(Achievement).filter(
            Achievement.user_id == user_id,
            Achievement.achievement_type == AchievementType.HABIT_COUNT,
            Achievement.is_completed == False
        ).all()
        completed = []
        for achievement in habit_achievements:
            if habit_count >= achievement.condition_value:
                if achievement.update_progress(habit_count):
                    completed.append(achievement)
        if completed:
            self.db.commit()
        return completed

    def check_completion_achievements(self, user_id: int, total_completions: int) -> List[Achievement]:
        """
        Проверяет достижения за общее количество выполнений
        """
        completion_achievements = self.db.query(Achievement).filter(
            Achievement.user_id == user_id,
            Achievement.achievement_type == AchievementType.COMPLETION,
            Achievement.is_completed == False
        ).all()
        completed = []
        for achievement in completion_achievements:
            if total_completions >= achievement.condition_value:
                if achievement.update_progress(total_completions):
                    completed.append(achievement)
        if completed:
            self.db.commit()
        return completed

    def check_stat_achievements(self, user_id: int, stats: Dict[StatType, int]) -> List[Achievement]:
        """
        Проверяет достижения за характеристики
        """
        stat_achievements = self.db.query(Achievement).filter(
            Achievement.user_id == user_id,
            Achievement.achievement_type == AchievementType.STAT,
            Achievement.is_completed == False
        ).all()
        completed = []
        for achievement in stat_achievements:
            for stat_type, value in stats.items():
                if value >= achievement.condition_value:
                    if achievement.update_progress(value):
                        completed.append(achievement)
                    break
        if completed:
            self.db.commit()
        return completed

    def get_achievement_progress(self, user_id: int) -> Dict[str, Any]:
        """
        Возвращает прогресс по всем достижениям
        """
        achievements = self.get_user_achievements(user_id)
        total = len(achievements)
        completed = sum(1 for a in achievements if a.is_completed)
        in_progress = total - completed
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "completion_rate": (completed / total * 100) if total > 0 else 0
        }