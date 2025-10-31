# Telegram Order Bot

This is a Telegram bot designed to automate digital product order management with a role-based system.

## Features

- **Role-Based Access:** Differentiates between 'Agent' (order creation) and 'Delivery' (order fulfillment) roles.
- **Authentication:** Password-protected access for bot users.
- **New Order Flow (Agent):** Guided process for selecting products, periods, payment methods, platforms, and entering contact details/comments.
- **Order Management (Delivery):** View pending orders, update order status (`Keep in Delivery` / `Complete`), and add delivery comments.
- **Database Logging:** Stores all order-related information, including timestamps and status updates.
- **Auto-Generated Order Numbers:** Unique order numbers for tracking.
- **Order Export:** Agents can download a CSV file of all their created orders.

## Tech Stack

- Python 3.9+
- `python-telegram-bot` library for Telegram Bot API interaction.
- `SQLAlchemy` for database ORM (SQLite by default, easily configurable for PostgreSQL).
- `python-dotenv` for environment variable management.

## Project Structure

```
order_bot/
├── config.py
├── database.py
├── models.py
├── main.py
├── README.md
├── requirements.txt
├── repository-structure.txt
├── handlers/
│   ├── __init__.py
│   ├── common.py
│   ├── auth.py
│   ├── agent.py
│   └── delivery.py
└── services/
    ├── __init__.py
    ├── user_service.py
    └── order_service.py
```

## Setup and Run Instructions

### 1. Clone the Repository

```bash
git clone <repository_url>
cd order_bot
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

- **On Windows:**
  ```bash
  .\venv\Scripts\activate
  ```
- **On macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory of the project (`order_bot/`) and add the following:

```
TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
# Optional: DATABASE_URL="postgresql://user:password@host:port/dbname" (defaults to sqlite:///order_bot.db)
```

- **`TELEGRAM_BOT_TOKEN`**: Obtain this token by talking to `@BotFather` on Telegram. Create a new bot and copy the HTTP API token.
- **`ADMIN_PASSWORD`**: The default password for authentication is `7759` (defined in `config.py`).
- **`DATABASE_URL`**: By default, the bot uses SQLite and creates a file named `order_bot.db` in the project root. If you want to use PostgreSQL or another database, provide the appropriate SQLAlchemy connection string here.

### 6. Run the Bot

```bash
python main.py
```

### 7. Interact with the Bot on Telegram

1. Open Telegram and find your bot.
2. Send the `/start` command.
3. The bot will prompt you for a password (`7759`).
4. After entering the correct password, select your role (`Confirmation (Agent)` or `Delivery (Responsible)`).
5. Based on your role, you will see the respective menu options.

### Agent Role (Confirmation)

- **New Order:** Follow the guided steps to create a new digital product order.
- **See All Orders:** View a list of all orders you have created.
- **Download Orders File:** Download a CSV file containing all your created orders.

### Delivery Role (Responsible User)

- **Orders Waiting Delivery:** View a list of orders that are awaiting delivery.
- Select an order to see its details.
- **Keep in Delivery:** Mark an order as 'In Delivery' (status remains 'Waiting Delivery' but you are assigned).
- **Complete:** Mark an order as 'Completed' and optionally add comments.

Enjoy managing your digital product orders!
