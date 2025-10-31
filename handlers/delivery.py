from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, CommandHandler
from sqlalchemy.orm import Session

from database import SessionLocal
from models import OrderStatus, User, UserRole
from services.order_service import (
    get_delivery_pending_orders,
    get_order_by_id,
    update_order_status,
    assign_delivery_user
)
from services.user_service import get_user_by_id
from handlers.common import delivery_main_menu_keyboard

# States for Delivery conversation
SELECT_ORDER, VIEW_ORDER, ENTER_DELIVERY_COMMENTS = range(3)

async def delivery_menu(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if query:
        await query.answer()
        if query.data == "orders_waiting_delivery":
            await show_orders_waiting_delivery(update, context)

async def show_orders_waiting_delivery(update: Update, context: CallbackContext) -> int:
    db: Session = SessionLocal()
    try:
        orders = get_delivery_pending_orders(db)
        if not orders:
            await update.callback_query.edit_message_text("No orders waiting for delivery.")
            await update.callback_query.message.reply_text("What else would you like to do?", reply_markup=delivery_main_menu_keyboard())
            return ConversationHandler.END

        buttons = []
        for order in orders:
            buttons.append([InlineKeyboardButton(f"{order.id} - {order.product.name}", callback_data=f"select_order_{order.id}")])
        buttons.append([InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="delivery_main_menu")])
        reply_markup = InlineKeyboardMarkup(buttons)

        await update.callback_query.edit_message_text(
            "Orders waiting for delivery:", reply_markup=reply_markup
        )
        return SELECT_ORDER
    finally:
        db.close()

async def select_delivery_order(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    order_id = query.data.replace("select_order_", "")
    context.user_data["selected_order_id"] = order_id

    db: Session = SessionLocal()
    try:
        order = get_order_by_id(db, order_id)
        if not order:
            await query.edit_message_text("Order not found.")
            await query.message.reply_text("What else would you like to do?", reply_markup=delivery_main_menu_keyboard())
            return ConversationHandler.END

        await view_order_details(update, context, order)
        return VIEW_ORDER
    finally:
        db.close()

async def view_order_details(update: Update, context: CallbackContext, order) -> None:
    details_text = (
        f"Order ID: {order.id}\n"
        f"Product: {order.product.name}\n"
        f"Period: {order.period.duration}\n"
        f"Payment Method: {order.payment_method.name}\n"
        f"Platform: {order.platform.name}\n"
        f"Contact Info: {order.contact_info}\n"
        f"Comments: {order.comments if order.comments else 'None'}\n"
        f"Status: {order.status.value}\n"
        f"Created At: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
    )

    buttons = [
        [InlineKeyboardButton("📦 Keep in Delivery", callback_data=f"keep_delivery_{order.id}")],
        [InlineKeyboardButton("✅ Complete", callback_data=f"complete_order_{order.id}")],
        [InlineKeyboardButton("⬅️ Back to Orders List", callback_data="orders_waiting_delivery")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.edit_message_text(details_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(details_text, reply_markup=reply_markup)

async def keep_in_delivery(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    order_id = query.data.replace("keep_delivery_", "")
    delivery_user_id = query.from_user.id

    db: Session = SessionLocal()
    try:
        order = update_order_status(db, order_id, OrderStatus.IN_DELIVERY, delivery_user_id=delivery_user_id)
        if order:
            await query.edit_message_text(f"Order {order.id} status updated to 'In Delivery'.")
        else:
            await query.edit_message_text("Failed to update order status.")
        await query.message.reply_text("What else would you like to do?", reply_markup=delivery_main_menu_keyboard())
        return ConversationHandler.END
    finally:
        db.close()

async def request_completion_comments(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    order_id = query.data.replace("complete_order_", "")
    context.user_data["order_to_complete_id"] = order_id

    await query.edit_message_text("Please enter any optional comments for the completion, or type 'no' if none:")
    return ENTER_DELIVERY_COMMENTS

async def complete_order(update: Update, context: CallbackContext) -> int:
    comments = update.message.text
    order_id = context.user_data["order_to_complete_id"]
    delivery_user_id = update.effective_user.id

    db: Session = SessionLocal()
    try:
        if comments.lower() == 'no':
            comments = None
        order = update_order_status(db, order_id, OrderStatus.COMPLETED, 
                                    delivery_user_id=delivery_user_id, delivery_comments=comments)
        if order:
            await update.message.reply_text(f"Order {order.id} marked as 'Completed'!")
        else:
            await update.message.reply_text("Failed to complete order.")
        
        context.user_data.pop("selected_order_id", None)
        context.user_data.pop("order_to_complete_id", None)
        await update.message.reply_text("What else would you like to do?", reply_markup=delivery_main_menu_keyboard())
        return ConversationHandler.END
    finally:
        db.close()

async def delivery_cancel(update: Update, context: CallbackContext) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Delivery operation cancelled.")
        await update.callback_query.message.reply_text("What else would you like to do?", reply_markup=delivery_main_menu_keyboard())
    else:
        await update.message.reply_text("Delivery operation cancelled.")
        await update.message.reply_text("What else would you like to do?", reply_markup=delivery_main_menu_keyboard())

    context.user_data.pop("selected_order_id", None)
    context.user_data.pop("order_to_complete_id", None)
    return ConversationHandler.END

delivery_conversation_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(delivery_menu, pattern="^orders_waiting_delivery$"),
    ],
    states={
        SELECT_ORDER: [
            CallbackQueryHandler(select_delivery_order, pattern="^select_order_"),
            CallbackQueryHandler(delivery_menu, pattern="^delivery_main_menu$")
        ],
        VIEW_ORDER: [
            CallbackQueryHandler(keep_in_delivery, pattern="^keep_delivery_"),
            CallbackQueryHandler(request_completion_comments, pattern="^complete_order_"),
            CallbackQueryHandler(show_orders_waiting_delivery, pattern="^orders_waiting_delivery$") # Back to orders list
        ],
        ENTER_DELIVERY_COMMENTS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, complete_order)
        ],
    },
    fallbacks=[
        CallbackQueryHandler(delivery_cancel, pattern="^delivery_main_menu$"),
        CommandHandler("cancel", delivery_cancel)
    ],
    map_to_parent={
        ConversationHandler.END: SELECT_ORDER # Transition back to the main delivery menu after conversation ends
    }
)
