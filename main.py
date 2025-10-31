import logging

from telegram.ext import Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram import Update

from config import TELEGRAM_BOT_TOKEN
from database import Base, engine, SessionLocal
from models import Product, Period, PaymentMethod, Platform
from handlers.auth import auth_conversation_handler
from handlers.agent import agent_conversation_handler
from handlers.delivery import delivery_conversation_handler
from handlers.common import agent_main_menu_keyboard, delivery_main_menu_keyboard
from services.user_service import get_user_by_id
from models import UserRole

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_authentication_menu(update, context):
    db = SessionLocal()
    try:
        user = get_user_by_id(db, update.effective_user.id)
        if user and user.is_authenticated:
            if user.role == UserRole.AGENT:
                await update.callback_query.edit_message_text("Welcome back, Agent!", reply_markup=agent_main_menu_keyboard())
            elif user.role == UserRole.DELIVERY:
                await update.callback_query.edit_message_text("Welcome back, Delivery Responsible!", reply_markup=delivery_main_menu_keyboard())
            else:
                await update.callback_query.edit_message_text("Your role is not set. Please contact an administrator.")
        else:
            await update.callback_query.edit_message_text("Please /start to authenticate.")
    finally:
        db.close()

def init_db_data():
    db = SessionLocal()
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)

        # Add Products
        products_data = [
            "Creative Cloud", "Perplexity", "Office 365", "Google AI Pro",
            "Coursera Plus", "LinkedIn", "Gamma", "Cursor", "Filmora Pro", "Eleven Labs"
        ]
        for p_name in products_data:
            if not db.query(Product).filter(Product.name == p_name).first():
                db.add(Product(name=p_name))
        
        # Add Periods
        periods_data = ["1 month", "3 months", "6 months", "12 months"]
        for p_duration in periods_data:
            if not db.query(Period).filter(Period.duration == p_duration).first():
                db.add(Period(duration=p_duration))

        # Add Payment Methods
        payment_methods_data = ["CIH Bank", "Barid Bank", "Tijjari/Wafa Bank"]
        for pm_name in payment_methods_data:
            if not db.query(PaymentMethod).filter(PaymentMethod.name == pm_name).first():
                db.add(PaymentMethod(name=pm_name))

        # Add Platforms
        platforms_data = ["WhatsApp", "Instagram"]
        for pl_name in platforms_data:
            if not db.query(Platform).filter(Platform.name == pl_name).first():
                db.add(Platform(name=pl_name))

        db.commit()
        logger.info("Database initialized with predefined data.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    # Initialize database and populate data
    init_db_data()

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(auth_conversation_handler)
    application.add_handler(agent_conversation_handler)
    application.add_handler(delivery_conversation_handler)
    application.add_handler(CallbackQueryHandler(post_authentication_menu, pattern="^agent_main_menu$|^delivery_main_menu$"))

    logger.info("Bot started polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
