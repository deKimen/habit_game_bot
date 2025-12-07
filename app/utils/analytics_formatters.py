from typing import Dict, Any, List, Optional
import base64
import io
from datetime import datetime, date, timedelta


def format_weekly_stats(stats_data: Dict[str, Any]) -> str:
    """
    Форматирует недельную статистику
    """
    if not stats_data.get("stats"):
        return "📊 **Аналитика за неделю**\n\nНет данных за последнюю неделю."
    summary = stats_data["summary"]
    stats = stats_data["stats"]
    days_text = []
    for stat in stats[-7:]:
        day_date = datetime.strptime(stat["date"], "%Y-%m-%d")
        day_name = day_date.strftime("%a")
        day_num = day_date.day
        completed = stat["habits_completed"]
        xp = stat["total_xp_gained"]
        day_emoji = "✅" if completed > 0 else "➖"
        days_text.append(f"{day_emoji} {day_name} {day_num}: {completed} привычек, +{xp} XP")
    text = (
        f"📊 **Аналитика за неделю**\n"
        f"📅 {stats_data['start_date']} - {stats_data['end_date']}\n\n"
        f"📈 **Сводка:**\n"
        f"✅ Выполнено привычек: {summary['total_completed']}\n"
        f"⭐ Получено опыта: {summary['total_xp']}\n"
        f"🏆 Достижений: {summary['total_achievements']}\n"
        f"📅 Активных дней: {summary['active_days']}/7\n"
        f"📊 Процент активности: {summary['completion_rate']:.1f}%\n\n"
        f"📋 **По дням:**\n"
    )
    text += "\n".join(days_text)
    text += f"\n\n📉 В среднем за день: {summary['avg_daily_completed']} привычек, {summary['avg_daily_xp']} XP"
    if summary.get("best_day"):
        text += f"\n\n🏆 **Лучший день:** {summary['best_day']['date']} ({summary['best_day']['completed']} привычек)"
    return text

def format_monthly_stats(stats_data: Dict[str, Any]) -> str:
    """
    Форматирует месячную статистику
    """
    if not stats_data.get("stats"):
        return "📈 **Аналитика за месяц**\n\nНет данных за последний месяц."
    summary = stats_data["summary"]
    stats = stats_data["stats"]
    weekly_groups = {}
    for stat in stats:
        day_date = datetime.strptime(stat["date"], "%Y-%m-%d")
        week_num = day_date.isocalendar()[1]  # Номер недели
        if week_num not in weekly_groups:
            weekly_groups[week_num] = []
        weekly_groups[week_num].append(stat)
    weeks_text = []
    for week_num, week_stats in sorted(weekly_groups.items()):
        week_completed = sum(s["habits_completed"] for s in week_stats)
        week_xp = sum(s["total_xp_gained"] for s in week_stats)
        week_days = len(week_stats)
        weeks_text.append(f"📅 Неделя {week_num}: {week_completed} привычек, +{week_xp} XP ({week_days} дней)")
    text = (
        f"📈 **Аналитика за 30 дней**\n"
        f"📅 {stats_data['start_date']} - {stats_data['end_date']}\n\n"
        f"📊 **Общая статистика:**\n"
        f"✅ Всего выполнено: {summary['total_completed']} привычек\n"
        f"⭐ Всего опыта: {summary['total_xp']}\n"
        f"🏆 Достижений: {summary['total_achievements']}\n"
        f"📅 Активных дней: {summary['active_days']}/30\n"
        f"📈 Процент активности: {summary['completion_rate']:.1f}%\n\n"
        f"📋 **По неделям:**\n"
    )
    text += "\n".join(weeks_text)
    text += f"\n\n📉 В среднем за день: {summary['avg_daily_completed']} привычек"
    return text

def format_habits_analytics(analytics: Dict[str, Any]) -> str:
    """
    Форматирует аналитику по привычкам
    """
    if not analytics:
        return "📝 **Аналитика привычек**\n\nУ тебя пока нет привычек."
    text = (
        f"📝 **Аналитика привычек**\n\n"
        f"📊 Всего привычек: {analytics['total_habits']}\n"
        f"✅ Всего выполнений: {analytics['total_completions']}\n"
        f"🔥 Общая длина серий: {analytics['total_streaks']} дней\n"
        f"📈 В среднем на привычку: {analytics['avg_completions_per_habit']} выполнений\n\n"
    )
    if analytics.get('habit_types'):
        text += "📅 **По типам:**\n"
        for habit_type, count in analytics['habit_types'].items():
            type_emoji = "📅" if habit_type == "daily" else "📆" if habit_type == "weekly" else "📝"
            text += f"{type_emoji} {habit_type}: {count}\n"
        text += "\n"
    if analytics.get('stat_distribution'):
        text += "🎯 **По характеристикам:**\n"
        emoji_map = {
            "strength": "💪",
            "agility": "🎯",
            "intelligence": "📚",
            "charisma": "🎭"
        }
        for stat, count in analytics['stat_distribution'].items():
            emoji = emoji_map.get(stat, "⚡")
            text += f"{emoji} {stat}: {count}\n"
        text += "\n"
    if analytics.get('top_streak_habits'):
        text += "🔥 **Топ привычек по сериям:**\n"
        for i, habit in enumerate(analytics['top_streak_habits'][:3], 1):
            text += f"{i}. {habit['name']}: {habit['streak']} дней ({habit['total_completions']} выполнений)\n"
    return text

def format_analytics_summary(user_id: int, analytics_service) -> str:
    """
    Форматирует сводку аналитики
    """
    weekly_stats = analytics_service.get_weekly_stats(user_id)
    habits_analytics = analytics_service.get_habits_analytics(user_id)
    if not weekly_stats.get("stats") or not habits_analytics:
        return "📊 **Сводка аналитики**\n\nНедостаточно данных для анализа."
    weekly_summary = weekly_stats["summary"]
    text = (
        f"📊 **Сводка аналитики**\n\n"
        f"📈 **Недельная активность:**\n"
        f"✅ {weekly_summary['total_completed']} привычек выполнено\n"
        f"⭐ {weekly_summary['total_xp']} опыта получено\n"
        f"📅 {weekly_summary['active_days']}/7 активных дней\n"
        f"📊 Активность: {weekly_summary['completion_rate']:.1f}%\n\n"
        f"📝 **Статистика привычек:**\n"
        f"🔢 Всего привычек: {habits_analytics['total_habits']}\n"
        f"✅ Всего выполнений: {habits_analytics['total_completions']}\n"
        f"🔥 Средняя серия: {habits_analytics['avg_completions_per_habit']:.1f} дней\n"
    )
    recommendations = []
    if weekly_summary['completion_rate'] < 50:
        recommendations.append("📉 Старайся быть более последовательным")
    elif weekly_summary['completion_rate'] > 80:
        recommendations.append("🎉 Отличная работа! Продолжай в том же духе!")
    if habits_analytics['total_habits'] < 3:
        recommendations.append("📝 Добавь больше привычек для лучшего прогресса")
    if recommendations:
        text += "\n💡 **Рекомендации:**\n"
        for rec in recommendations:
            text += f"• {rec}\n"
    return text