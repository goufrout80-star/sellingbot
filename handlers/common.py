from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import ROLE_AGENT, ROLE_DELIVERY

def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return InlineKeyboardMarkup(menu)

def agent_main_menu_keyboard():
    buttons = [
        InlineKeyboardButton("➕ New Order", callback_data="new_order"),
        InlineKeyboardButton("📋 See All Orders", callback_data="see_all_orders"),
        InlineKeyboardButton("⬇️ Download Orders File", callback_data="download_orders_file"),
    ]
    return build_menu(buttons, n_cols=1)

def delivery_main_menu_keyboard():
    buttons = [
        InlineKeyboardButton("📦 Orders Waiting Delivery", callback_data="orders_waiting_delivery"),
    ]
    return build_menu(buttons, n_cols=1)
