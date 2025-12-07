import io
import base64
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from app.models.stats import DailyStats
from app.models.habit import Habit, HabitType, StatType
from app.models.achievements import Achievement
from app.services.habit_service import HabitService
from app.services.achieve_service import AchievementService


class AnalyticsService:
    """Сервис для аналитики и визуализации"""

    def __init__(self, db: Session):
        self.db = db
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")

    def record_daily_stats(self, user_id: int, stat_date: date = None) -> DailyStats:
        """
        Записывает ежедневную статистику пользователя
        """
        if stat_date is None:
            stat_date = date.today()

        # Проверяем, есть ли уже запись за сегодня
        existing = self.db.query(DailyStats).filter(
            DailyStats.user_id == user_id,
            func.date(DailyStats.stat_date) == stat_date
        ).first()

        if existing:
            return existing

        habit_service = HabitService(self.db)
        achievement_service = AchievementService(self.db)
        habits = habit_service.get_user_habits(user_id, active_only=True)
        stats = DailyStats(
            user_id=user_id,
            stat_date=stat_date,
            habits_completed=0,
            total_xp_gained=0,
            streaks_maintained=0,
            achievements_unlocked=0
        )
        self.db.add(stats)
        self.db.commit()
        self.db.refresh(stats)

        return stats

    def update_stats_after_completion(self, user_id: int, habit: Habit, xp_gained: int) -> None:
        """
        Обновляет статистику после выполнения привычки
        """
        today = date.today()

        # Получаем или создаем запись за сегодня
        stats = self.record_daily_stats(user_id, today)

        # Обновляем статистику
        stats.habits_completed += 1
        stats.total_xp_gained += xp_gained

        # Обновляем статистику по типам привычек
        if habit.stat_bonus == StatType.STRENGTH:
            stats.strength_habits += 1
        elif habit.stat_bonus == StatType.AGILITY:
            stats.agility_habits += 1
        elif habit.stat_bonus == StatType.INTELLIGENCE:
            stats.intelligence_habits += 1
        elif habit.stat_bonus == StatType.CHARISMA:
            stats.charisma_habits += 1

        # Проверяем серию
        if habit.current_streak > 1:
            stats.streaks_maintained += 1

        self.db.commit()

    def update_achievement_stats(self, user_id: int) -> None:
        """
        Обновляет статистику достижений
        """
        today = date.today()
        stats = self.record_daily_stats(user_id, today)
        achievement_service = AchievementService(self.db)
        achievements = achievement_service.get_user_achievements(user_id, completed_only=True)
        today_achievements = sum(
            1 for a in achievements
            if a.completed_at and a.completed_at.date() == today
        )
        stats.achievements_unlocked = today_achievements
        self.db.commit()

    def get_weekly_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Получает статистику за последнюю неделю
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=6)
        stats = self.db.query(DailyStats).filter(
            DailyStats.user_id == user_id,
            DailyStats.stat_date.between(start_date, end_date)
        ).order_by(DailyStats.stat_date).all()
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            all_dates.append(current_date)
            current_date += timedelta(days=1)
        stats_dict = {s.stat_date.date(): s for s in stats}
        filled_stats = []
        for d in all_dates:
            if d in stats_dict:
                filled_stats.append(stats_dict[d])
            else:
                empty_stat = DailyStats(
                    user_id=user_id,
                    stat_date=d,
                    habits_completed=0,
                    total_xp_gained=0
                )
                filled_stats.append(empty_stat)
        return {
            "period": "weekly",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "stats": [s.to_dict() for s in filled_stats],
            "summary": self._calculate_summary(filled_stats)
        }

    def get_monthly_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Получает статистику за последний месяц
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=29)  # 30 дней включая сегодня
        stats = self.db.query(DailyStats).filter(
            DailyStats.user_id == user_id,
            DailyStats.stat_date.between(start_date, end_date)
        ).order_by(DailyStats.stat_date).all()
        return {
            "period": "monthly",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "stats": [s.to_dict() for s in stats],
            "summary": self._calculate_summary(stats)
        }

    def _calculate_summary(self, stats: List[DailyStats]) -> Dict[str, Any]:
        """Рассчитывает сводную статистику"""
        if not stats:
            return {}
        total_completed = sum(s.habits_completed for s in stats)
        total_xp = sum(s.total_xp_gained for s in stats)
        total_achievements = sum(s.achievements_unlocked for s in stats)
        total_days = len(stats)
        active_days = sum(1 for s in stats if s.habits_completed > 0)
        avg_completed = total_completed / total_days if total_days > 0 else 0
        avg_xp = total_xp / total_days if total_days > 0 else 0
        best_day = max(stats, key=lambda x: x.habits_completed, default=None)
        return {
            "total_completed": total_completed,
            "total_xp": total_xp,
            "total_achievements": total_achievements,
            "active_days": active_days,
            "completion_rate": (active_days / total_days * 100) if total_days > 0 else 0,
            "avg_daily_completed": round(avg_completed, 1),
            "avg_daily_xp": round(avg_xp, 1),
            "best_day": {
                "date": best_day.stat_date.strftime("%Y-%m-%d") if best_day else None,
                "completed": best_day.habits_completed if best_day else 0
            } if best_day else None
        }

    def create_completion_chart(self, user_id: int, period: str = "weekly") -> Optional[str]:
        """
        Создает график выполнения привычек.
        Возвращает base64 строку с изображением
        """
        if period == "weekly":
            data = self.get_weekly_stats(user_id)
            title = "Выполнение привычек за неделю"
        else:
            data = self.get_monthly_stats(user_id)
            title = "Выполнение привычек за месяц"
        if not data["stats"]:
            return None
        df = pd.DataFrame(data["stats"])
        df['date'] = pd.to_datetime(df['date'])
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        ax1.bar(df['date'].dt.strftime('%d.%m'), df['habits_completed'], color='skyblue', edgecolor='black')
        ax1.set_title(f'{title} - Выполненные привычки', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Дата')
        ax1.set_ylabel('Количество привычек')
        ax1.grid(True, alpha=0.3)
        for i, v in enumerate(df['habits_completed']):
            ax1.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
        stat_types = ['strength', 'agility', 'intelligence', 'charisma']
        stat_data = []
        for stat_type in stat_types:
            total = sum(df['stat_distribution'].apply(lambda x: x.get(stat_type, 0)))
            stat_data.append(total)
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        wedges, texts, autotexts = ax2.pie(
            stat_data,
            labels=['Сила', 'Ловкость', 'Интеллект', 'Харизма'],
            colors=colors,
            autopct='%1.1f%%',
            startangle=90
        )
        ax2.set_title('Распределение по характеристикам', fontsize=14, fontweight='bold')
        plt.suptitle(title, fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        return img_base64

    def create_progress_chart(self, user_id: int) -> Optional[str]:
        """
        Создает график прогресса уровня и опыта
        """
        levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        xp_required = [lvl * 100 for lvl in levels]
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(levels, xp_required, 'o-', linewidth=2, markersize=8,
                color='#4ECDC4', label='Требуемый опыт')
        ax.fill_between(levels, 0, xp_required, alpha=0.2, color='#4ECDC4')
        ax.set_title('Прогресс прокачки персонажа', fontsize=16, fontweight='bold')
        ax.set_xlabel('Уровень', fontsize=12)
        ax.set_ylabel('Опыт', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend()
        for i, (lvl, xp) in enumerate(zip(levels, xp_required)):
            ax.annotate(f'{xp} XP', (lvl, xp), textcoords="offset points",
                        xytext=(0, 10), ha='center', fontsize=9)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        return img_base64

    def get_habits_analytics(self, user_id: int) -> Dict[str, Any]:
        """
        Аналитика по привычкам
        """
        from app.services.habit_service import HabitService
        habit_service = HabitService(self.db)
        habits = habit_service.get_user_habits(user_id, active_only=True)
        if not habits:
            return {}
        habit_types = {}
        for habit in habits:
            habit_type = habit.habit_type.value
            habit_types[habit_type] = habit_types.get(habit_type, 0) + 1
        stat_distribution = {}
        for habit in habits:
            stat = habit.stat_bonus.value
            stat_distribution[stat] = stat_distribution.get(stat, 0) + 1
        top_streak_habits = sorted(
            habits,
            key=lambda x: x.current_streak,
            reverse=True
        )[:3]
        total_completions = sum(h.total_completions for h in habits)
        total_streaks = sum(h.current_streak for h in habits)
        avg_completions = total_completions / len(habits) if habits else 0
        return {
            "total_habits": len(habits),
            "habit_types": habit_types,
            "stat_distribution": stat_distribution,
            "total_completions": total_completions,
            "total_streaks": total_streaks,
            "avg_completions_per_habit": round(avg_completions, 1),
            "top_streak_habits": [
                {
                    "name": h.name,
                    "streak": h.current_streak,
                    "total_completions": h.total_completions
                }
                for h in top_streak_habits
            ]
        }