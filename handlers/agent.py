import io
import csv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import CallbackContext, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, CommandHandler
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Product, Period, PaymentMethod, Platform, OrderStatus
from services.order_service import create_order, get_all_orders
from services.user_service import get_user_by_id
from handlers.common import agent_main_menu_keyboard

# States for New Order conversation
(SELECT_PRODUCT, SELECT_PERIOD, SELECT_PAYMENT_METHOD, SELECT_PLATFORM, 
 ENTER_CONTACT_INFO, ENTER_COMMENTS, CONFIRM_ORDER) = range(7)

async def agent_menu(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        if query.data == "new_order":
            return await new_order_start(update, context)
        elif query.data == "see_all_orders":
            await see_all_orders(update, context)
        elif query.data == "download_orders_file":
            await download_orders_file(update, context)
        elif query.data == "agent_main_menu":
            await update.callback_query.edit_message_text("Welcome back, Agent!", reply_markup=agent_main_menu_keyboard())
            return ConversationHandler.END
    return ConversationHandler.END

async def new_order_start(update: Update, context: CallbackContext) -> int:
    db: Session = SessionLocal()
    try:
        products = db.query(Product).all()
        buttons = [[InlineKeyboardButton(p.name, callback_data=f"new_order_product_{p.name}")] for p in products]
        buttons.append([InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="agent_main_menu")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.callback_query.edit_message_text(
            "Please select a product:", reply_markup=reply_markup
        )
        return SELECT_PRODUCT
    finally:
        db.close()

async def select_product(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    product_name = query.data.replace("new_order_product_", "")
    context.user_data["new_order"] = {"product": product_name}

    db: Session = SessionLocal()
    try:
        periods = db.query(Period).all()
        buttons = [[InlineKeyboardButton(p.duration, callback_data=f"new_order_period_{p.duration}")] for p in periods]
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"new_order_product_{context.user_data['new_order']['product']}")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            f"You selected {product_name}. Now, please select the period:", reply_markup=reply_markup
        )
        return SELECT_PERIOD
    finally:
        db.close()

async def select_period(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    period_duration = query.data.replace("new_order_period_", "")
    context.user_data["new_order"]["period"] = period_duration

    db: Session = SessionLocal()
    try:
        payment_methods = db.query(PaymentMethod).all()
        buttons = [[InlineKeyboardButton(pm.name, callback_data=f"new_order_payment_{pm.name}")] for pm in payment_methods]
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"new_order_period_{context.user_data['new_order']['period']}")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            f"You selected {period_duration}. Now, please select the payment method:", reply_markup=reply_markup
        )
        return SELECT_PAYMENT_METHOD
    finally:
        db.close()

async def select_payment_method(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    payment_method_name = query.data.replace("new_order_payment_", "")
    context.user_data["new_order"]["payment_method"] = payment_method_name

    db: Session = SessionLocal()
    try:
        platforms = db.query(Platform).all()
        buttons = [[InlineKeyboardButton(pl.name, callback_data=f"new_order_platform_{pl.name}")] for pl in platforms]
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"new_order_payment_{context.user_data['new_order']['payment_method']}")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            f"You selected {payment_method_name}. Now, please select the platform:", reply_markup=reply_markup
        )
        return SELECT_PLATFORM
    finally:
        db.close()

async def select_platform(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    platform_name = query.data.replace("new_order_platform_", "")
    context.user_data["new_order"]["platform"] = platform_name

    await query.edit_message_text(
        f"You selected {platform_name}. Please enter the username or contact info for the order:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=f"new_order_platform_{context.user_data['new_order']['platform']}")]])
    )
    return ENTER_CONTACT_INFO

async def enter_contact_info(update: Update, context: CallbackContext) -> int:
    contact_info = update.message.text
    context.user_data["new_order"]["contact_info"] = contact_info

    await update.message.reply_text(
        "Please enter any optional comments for the order, or type 'no' if none:"
    )
    return ENTER_COMMENTS

async def enter_comments(update: Update, context: CallbackContext) -> int:
    comments = update.message.text
    if comments.lower() != 'no':
        context.user_data["new_order"]["comments"] = comments
    else:
        context.user_data["new_order"]["comments"] = None

    order_data = context.user_data["new_order"]
    confirmation_text = (
        "Please confirm your order details:\n\n"
        f"Product: {order_data['product']}\n"
        f"Period: {order_data['period']}\n"
        f"Payment Method: {order_data['payment_method']}\n"
        f"Platform: {order_data['platform']}\n"
        f"Contact Info: {order_data['contact_info']}\n"
        f"Comments: {order_data.get('comments', 'None')}\n\n"
        "Is this correct?"
    )
    buttons = [
        [InlineKeyboardButton("✅ Confirm", callback_data="confirm_new_order")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_new_order_flow")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(confirmation_text, reply_markup=reply_markup)
    return CONFIRM_ORDER

async def confirm_order(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    order_data = context.user_data["new_order"]
    user_id = query.from_user.id

    db: Session = SessionLocal()
    try:
        order = create_order(
            db,
            agent_id=user_id,
            product_name=order_data["product"],
            period_duration=order_data["period"],
            payment_method_name=order_data["payment_method"],
            platform_name=order_data["platform"],
            contact_info=order_data["contact_info"],
            comments=order_data.get("comments"),
        )
        await query.edit_message_text(f"Order {order.id} created successfully and set to 'Waiting Delivery'!")
        # Clear user_data for next order
        context.user_data.pop("new_order", None)
        await query.message.reply_text("What else would you like to do?", reply_markup=agent_main_menu_keyboard())
        return ConversationHandler.END
    except ValueError as e:
        await query.edit_message_text(f"Error creating order: {e}")
        await query.message.reply_text("Please try again or cancel.", reply_markup=agent_main_menu_keyboard())
        return ConversationHandler.END
    finally:
        db.close()

async def cancel_new_order_flow(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.pop("new_order", None)
    await query.edit_message_text("Order creation cancelled.")
    await query.message.reply_text("What else would you like to do?", reply_markup=agent_main_menu_keyboard())
    return ConversationHandler.END

async def see_all_orders(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    db: Session = SessionLocal()
    try:
        orders = get_all_orders(db) # This gets all orders, for agent it should be orders created by agent
        user = get_user_by_id(db, query.from_user.id)

        if not orders:
            await query.edit_message_text("No orders found.")
            await query.message.reply_text("What else would you like to do?", reply_markup=agent_main_menu_keyboard())
            return
        
        order_list_text = "Your Orders:\n\n"
        for order in orders:
            if order.agent_id == user.id: # Filter by agent ID
                order_list_text += (
                    f"Order ID: {order.id}\n"
                    f"Product: {order.product.name}\n"
                    f"Period: {order.period.duration}\n"
                    f"Status: {order.status.value}\n"
                    f"Created At: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"---\n"
                )
        await query.edit_message_text(order_list_text)
        await query.message.reply_text("What else would you like to do?", reply_markup=agent_main_menu_keyboard())
    finally:
        db.close()

async def download_orders_file(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    db: Session = SessionLocal()
    try:
        orders = get_all_orders(db) # Again, this needs to be filtered by agent_id later
        user = get_user_by_id(db, query.from_user.id)

        if not orders:
            await query.edit_message_text("No orders found to download.")
            await query.message.reply_text("What else would you like to do?", reply_markup=agent_main_menu_keyboard())
            return

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Order ID", "Agent ID", "Delivery User ID", "Product", "Period", "Payment Method", 
                         "Platform", "Contact Info", "Comments", "Status", "Created At", 
                         "Delivery Started At", "Completed At", "Delivery Comments"])

        for order in orders:
            if order.agent_id == user.id: # Filter by agent ID
                writer.writerow([
                    order.id,
                    order.agent_id,
                    order.delivery_user_id,
                    order.product.name,
                    order.period.duration,
                    order.payment_method.name,
                    order.platform.name,
                    order.contact_info,
                    order.comments,
                    order.status.value,
                    order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else '',
                    order.delivery_started_at.strftime('%Y-%m-%d %H:%M:%S') if order.delivery_started_at else '',
                    order.completed_at.strftime('%Y-%m-%d %H:%M:%S') if order.completed_at else '',
                    order.delivery_comments
                ])
        
        output.seek(0)
        file_data = InputFile(output.getvalue().encode('utf-8'), filename="orders.csv")
        await query.message.reply_document(document=file_data, caption="Here is your orders file.")
        await query.message.reply_text("What else would you like to do?", reply_markup=agent_main_menu_keyboard())
    finally:
        db.close()

agent_conversation_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(agent_menu, pattern="^new_order$"),
        CallbackQueryHandler(agent_menu, pattern="^see_all_orders$"),
        CallbackQueryHandler(agent_menu, pattern="^download_orders_file$"),
    ],
    states={
        SELECT_PRODUCT: [
            CallbackQueryHandler(select_product, pattern="^new_order_product_"),
            CallbackQueryHandler(agent_menu, pattern="^agent_main_menu$")
        ],
        SELECT_PERIOD: [
            CallbackQueryHandler(select_period, pattern="^new_order_period_"),
            CallbackQueryHandler(new_order_start, pattern="^new_order$") # Back to product selection
        ],
        SELECT_PAYMENT_METHOD: [
            CallbackQueryHandler(select_payment_method, pattern="^new_order_payment_"),
            CallbackQueryHandler(select_product, pattern="^new_order_product_") # Back to period selection
        ],
        SELECT_PLATFORM: [
            CallbackQueryHandler(select_platform, pattern="^new_order_platform_"),
            CallbackQueryHandler(select_period, pattern="^new_order_period_") # Back to payment method selection
        ],
        ENTER_CONTACT_INFO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contact_info),
            CallbackQueryHandler(select_platform, pattern="^new_order_platform_") # Back to platform selection
        ],
        ENTER_COMMENTS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, enter_comments)
        ],
        CONFIRM_ORDER: [
            CallbackQueryHandler(confirm_order, pattern="^confirm_new_order$"),
            CallbackQueryHandler(cancel_new_order_flow, pattern="^cancel_new_order_flow$")
        ],
    },
    fallbacks=[
        CallbackQueryHandler(cancel_new_order_flow, pattern="^cancel_new_order_flow$"),
        CommandHandler("cancel", cancel_new_order_flow)
    ],
    map_to_parent={
        ConversationHandler.END: 0 # Returning to a 'start' state for a smoother transition to the main menu.
    }
)
