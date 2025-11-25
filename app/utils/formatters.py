from typing import List
from app.models.habit import Habit


def format_habits_list(habits: List[Habit]) -> str:
    """
    Форматирует список привычек в красивый текст
    """
    if not habits:
        return "📝 У тебя пока нет привычек. Используй /newhabit чтобы добавить!"

    lines = ["📋 **Твои привычки:**\n"]

    for i, habit in enumerate(habits, 1):
        status_emoji = "✅" if habit.is_due_today() else "⏳"
        streak_emoji = "🔥" if habit.current_streak > 0 else "⚪"
        stat_emoji = _get_stat_emoji(habit.stat_bonus)

        lines.append(
            f"{i}. {status_emoji} **{habit.name}**\n"
            f"   {stat_emoji} {habit.stat_bonus.value} | "
            f"{streak_emoji} {habit.current_streak} дней | "
            f"ID: {habit.id}"
        )

    lines.append(f"\n🎯 Всего привычек: {len(habits)}")
    lines.append("ℹ️ Используй /done <ID> чтобы отметить выполнение")

    return "\n".join(lines)


def format_today_habits(habits: List[Habit]) -> str:
    """
    Форматирует список привычек на сегодня
    """
    if not habits:
        return "🎉 На сегодня все привычки выполнены! Или добавь новые через /newhabit"

    lines = ["📅 **Привычки на сегодня:**\n"]

    for i, habit in enumerate(habits, 1):
        stat_emoji = _get_stat_emoji(habit.stat_bonus)
        streak_info = f"🔥 {habit.current_streak}" if habit.current_streak > 0 else "Новая"

        lines.append(
            f"{i}. **{habit.name}**\n"
            f"   {stat_emoji} +{habit.xp_reward} XP | "
            f"{streak_info} | "
            f"ID: {habit.id}"
        )

    lines.append(f"\n💡 Используй /done <ID> чтобы отметить выполнение")

    return "\n".join(lines)


def _get_stat_emoji(stat_type) -> str:
    """Возвращает emoji для характеристики"""
    emoji_map = {
        "strength": "💪",
        "agility": "🎯",
        "intelligence": "📚",
        "charisma": "🎭"
    }
    return emoji_map.get(stat_type.value, "⚡")