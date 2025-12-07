from typing import List, Dict, Any
from app.models.customization import CustomizationType


def format_customization_item(customization: Dict[str, Any]) -> str:
    """
    Форматирует один элемент кастомизации
    """
    status_emoji = "✅" if customization["is_active"] else "🔓" if customization["is_unlocked"] else "🔒"
    return (
        f"{status_emoji} {customization['icon']} **{customization['name']}**\n"
        f"   📝 {customization['description']}\n"
        f"   🆔 ID: {customization['id']}"
    )

def format_customizations_list(customizations: List[Dict[str, Any]],
                               customization_type: CustomizationType) -> str:
    """
    Форматирует список кастомизаций
    """
    type_names = {
        CustomizationType.SKIN: "скины",
        CustomizationType.TITLE: "титулы",
        CustomizationType.BADGE: "значки",
        CustomizationType.COLOR: "цвета",
        CustomizationType.ANIMATION: "анимации"
    }
    type_name = type_names.get(customization_type, "элементы")
    if not customizations:
        return f"🎨 У тебя пока нет {type_name}. Повышай уровень чтобы получить новые!"
    customizations.sort(key=lambda x: (not x["is_active"], not x["is_unlocked"], x["name"]))
    lines = [f"🎨 **Твои {type_name}:**\n"]
    for custom in customizations:
        lines.append(format_customization_item(custom))
    lines.append(f"\n💡 Используй /activate <ID> чтобы выбрать {type_name[:-1]}")
    return "\n".join(lines)


def format_active_customizations(active_customs: Dict[CustomizationType, Dict[str, Any]]) -> str:
    """
    Форматирует активные кастомизации
    """
    if not active_customs:
        return "🎭 **Текущий вид персонажа:**\nСтандартный (используй /customize чтобы изменить)"
    lines = ["🎭 **Текущий вид персонажа:**\n"]
    type_names = {
        CustomizationType.SKIN: "Внешность",
        CustomizationType.TITLE: "Титул",
        CustomizationType.BADGE: "Значок",
        CustomizationType.COLOR: "Цвет",
        CustomizationType.ANIMATION: "Анимация"
    }
    for custom_type, custom_data in active_customs.items():
        type_name = type_names.get(custom_type, custom_type.value)
        lines.append(f"{custom_data['icon']} **{type_name}:** {custom_data['name']}")
    lines.append("\n💡 Используй /customize чтобы изменить внешний вид")
    return "\n".join(lines)

def format_customization_unlock(customization_data: Dict[str, Any]) -> str:
    """
    Сообщение о разблокировке кастомизации
    """
    customization = customization_data["customization"]
    return (
        f"🎉 **НОВАЯ КАСТОМИЗАЦИЯ!** 🎉\n\n"
        f"{customization.icon} **{customization.name}**\n"
        f"📝 {customization.description}\n\n"
        f"✨ Новый элемент разблокирован!\n"
        f"🎨 Используй /customize чтобы применить"
    )