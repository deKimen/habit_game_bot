from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.habit import Habit, HabitType
from app.models.character import StatType


class HabitService:
    """Сервис для работы с привычками"""

    def __init__(self, db: Session):
        self.db = db

    def create_habit(self, user_id: int, name: str, habit_type: HabitType,
                     stat_bonus: StatType, description: Optional[str] = None) -> Habit:
        """
        Создает новую привычку
        """
        habit = Habit(
            user_id=user_id,
            name=name,
            description=description,
            habit_type=habit_type,
            stat_bonus=stat_bonus,
            xp_reward=self._calculate_xp_reward(habit_type)
        )

        self.db.add(habit)
        self.db.commit()
        self.db.refresh(habit)

        return habit

    def get_user_habits(self, user_id: int, active_only: bool = True) -> List[Habit]:
        """
        Получает привычки пользователя
        """
        query = self.db.query(Habit).filter(Habit.user_id == user_id)

        if active_only:
            query = query.filter(Habit.is_active == True)

        return query.order_by(Habit.created_at.desc()).all()

    def get_habit_by_id(self, habit_id: int, user_id: int) -> Optional[Habit]:
        """
        Получает привычку по ID с проверкой владельца
        """
        return self.db.query(Habit).filter(
            Habit.id == habit_id,
            Habit.user_id == user_id
        ).first()

    def get_today_habits(self, user_id: int) -> List[Habit]:
        """
        Получает привычки, которые нужно выполнить сегодня
        """
        habits = self.get_user_habits(user_id, active_only=True)
        return [habit for habit in habits if habit.is_due_today()]

    def delete_habit(self, habit_id: int, user_id: int) -> bool:
        """
        Удаляет привычку (мягкое удаление)
        """
        habit = self.get_habit_by_id(habit_id, user_id)
        if not habit:
            return False

        habit.is_active = False
        self.db.commit()
        return True

    def _calculate_xp_reward(self, habit_type: HabitType) -> int:
        """
        Рассчитывает награду в опыте в зависимости от типа привычки
        """
        rewards = {
            HabitType.DAILY: 10,
            HabitType.WEEKLY: 25,
            HabitType.CUSTOM: 15
        }
        return rewards.get(habit_type, 10)

    def get_habit_stats(self, user_id: int) -> dict:
        """
        Возвращает статистику по привычкам пользователя
        """
        habits = self.get_user_habits(user_id, active_only=True)

        if not habits:
            return {
                "total_habits": 0,
                "active_streaks": 0,
                "total_completions": 0,
                "today_habits": 0
            }

        today_habits = self.get_today_habits(user_id)
        active_streaks = sum(1 for h in habits if h.current_streak > 0)
        total_completions = sum(h.total_completions for h in habits)

        return {
            "total_habits": len(habits),
            "active_streaks": active_streaks,
            "total_completions": total_completions,
            "today_habits": len(today_habits)
        }