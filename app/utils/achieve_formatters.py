from typing import List
from app.models.achievements import Achievement


def format_achievement(achievement: Achievement) -> str:
    """
    Форматирует одно достижение
    """
    status_emoji = "✅" if achievement.is_completed else "⏳"
    progress_bar = _create_progress_bar(achievement.progress, achievement.condition_value)
    return (
        f"{status_emoji} **{achievement.name}**\n"
        f"   📝 {achievement.description}\n"
        f"   {progress_bar} {achievement.progress}/{achievement.condition_value}\n"
        f"   🎁 Награда: +{achievement.reward_xp} XP"
    )

def format_achievements_list(achievements: List[Achievement]) -> str:
    """
    Форматирует список достижений
    """
    if not achievements:
        return "📭 У тебя пока нет достижений. Выполняй задания, чтобы их получать!"
    completed = [a for a in achievements if a.is_completed]
    in_progress = [a for a in achievements if not a.is_completed]
    lines = ["🏆 **Твои достижения:**\n"]
    if completed:
        lines.append("\n✅ **Полученные:**")
        for achievement in completed[:5]:  # Показываем только 5 последних
            lines.append(f"• {achievement.name} (+{achievement.reward_xp} XP)")
    if in_progress:
        lines.append("\n⏳ **В процессе:**")
        for achievement in in_progress[:10]:  # Показываем 10 ближайших
            lines.append(format_achievement(achievement))

    # Статистика
    total = len(achievements)
    completed_count = len(completed)
    completion_rate = (completed_count / total * 100) if total > 0 else 0
    lines.append(f"\n📊 **Статистика:** {completed_count}/{total} ({completion_rate:.1f}%)")
    return "\n".join(lines)

def format_achievement_unlock(achievement: Achievement) -> str:
    """
    Сообщение о разблокировке достижения
    """
    return (
        f"🎉 **НОВОЕ ДОСТИЖЕНИЕ!** 🎉\n\n"
        f"🏆 **{achievement.name}**\n"
        f"📝 {achievement.description}\n\n"
        f"⭐ **Награда:** +{achievement.reward_xp} опыта!\n"
        f"🎊 Поздравляем!"
    )

def _create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """
    Создает текстовый прогресс-бар
    """
    if total == 0:
        return "[          ]"
    filled = int((current / total) * length)
    filled = min(filled, length)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"