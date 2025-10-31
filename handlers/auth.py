from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, MessageHandler, CommandHandler, CallbackQueryHandler, ConversationHandler, filters

from config import ADMIN_PASSWORD, ROLE_AGENT, ROLE_DELIVERY
from database import SessionLocal
from services.user_service import get_or_create_user, set_user_authenticated, set_user_role, get_user_by_id
from models import UserRole, User
from handlers.common import agent_main_menu_keyboard, delivery_main_menu_keyboard

# States for authentication conversation
AUTH_PASSWORD, AUTH_ROLE = range(2)

async def start(update: Update, context: CallbackContext) -> int:
    db = SessionLocal()
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name

        user = get_or_create_user(db, user_id, username, first_name, last_name)

        if user.is_authenticated:
            await send_role_menu(update, context, user)
            return ConversationHandler.END
        else:
            await update.message.reply_text("Welcome! Please enter the password to access the bot.")
            return AUTH_PASSWORD
    finally:
        db.close()

async def authenticate_password(update: Update, context: CallbackContext) -> int:
    password = update.message.text
    db = SessionLocal()
    try:
        user_id = update.effective_user.id
        user = get_user_by_id(db, user_id)

        if password == ADMIN_PASSWORD:
            set_user_authenticated(db, user_id, True)
            await update.message.reply_text(
                "Password correct! Please select your role:",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Confirmation (Agent)", callback_data=f"set_role_{ROLE_AGENT}")],
                        [InlineKeyboardButton("Delivery (Responsible)", callback_data=f"set_role_{ROLE_DELIVERY}")],
                    ]
                ),
            )
            return AUTH_ROLE
        else:
            await update.message.reply_text("Incorrect password. Please try again.")
            return AUTH_PASSWORD
    finally:
        db.close()

async def set_role(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    db = SessionLocal()
    try:
        user_id = query.from_user.id
        role_str = query.data.replace("set_role_", "")
        role = UserRole(role_str) # Convert string to Enum

        set_user_role(db, user_id, role)
        user = get_user_by_id(db, user_id) # Refresh user object

        await query.edit_message_text(f"Your role has been set to {role.value}.")
        await send_role_menu(update, context, user)
        return ConversationHandler.END
    finally:
        db.close()

async def send_role_menu(update: Update, context: CallbackContext, user: User):
    if user.role == UserRole.AGENT:
        reply_markup = agent_main_menu_keyboard()
        message_text = "Welcome, Agent! How can I help you today?"
    elif user.role == UserRole.DELIVERY:
        reply_markup = delivery_main_menu_keyboard()
        message_text = "Welcome, Delivery Responsible! Here are the orders waiting for delivery:"
    else:
        reply_markup = None
        message_text = "Your role is not set. Please contact an administrator."

    if update.callback_query:
        await update.callback_query.message.reply_text(message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup)

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Authentication cancelled.")
    return ConversationHandler.END

auth_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        AUTH_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, authenticate_password)],
        AUTH_ROLE: [CallbackQueryHandler(set_role, pattern="^set_role_")]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
