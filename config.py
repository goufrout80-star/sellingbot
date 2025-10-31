import os
# from dotenv import load_dotenv

# load_dotenv()

TELEGRAM_BOT_TOKEN = "8314044757:AAFQ_nH0-mM1tMDkp6SjAASjmo0FFKfFoN8"
ADMIN_PASSWORD = "7759"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///order_bot.db")

# Roles
ROLE_AGENT = "Agent"
ROLE_DELIVERY = "Delivery"
