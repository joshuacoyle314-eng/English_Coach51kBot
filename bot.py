import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
import db
from vocab_data import get_word_of_the_day, get_random_quiz_question
from coach_ai import get_coaching_reply

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# In-memory conversation history per user (kept short; not critical to persist)
CONVO_HISTORY: dict[int, list[dict]] = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.username or "", user.first_name or "")
    text = (
        f"Hi {user.first_name}! I'm your English Coach. 🎓\n\n"
        "Just send me a message and I'll chat with you while correcting your "
        "grammar and mistakes along the way.\n\n"
        "Commands:\n"
        "/practice - tips on how conversation practice works\n"
        "/quiz - a multiple-choice vocabulary quiz\n"
        "/word - today's word of the day\n"
        "/progress - see your stats\n"
        "/help - show this message again"
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def practice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Just type any sentence or message in English, about any topic you like "
        "(your day, a hobby, an opinion). I'll reply, correct any mistakes, and "
        "keep the conversation going. Try it now!"
    )


async def word_of_the_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    w = get_word_of_the_day()
    text = (
        f"📖 Word of the Day: *{w['word']}*\n\n"
        f"Definition: {w['definition']}\n"
        f"Example: _{w['example']}_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = get_random_quiz_question()
    context.user_data["quiz_correct_answer"] = q["correct_definition"]
    context.user_data["quiz_word"] = q["word"]

    buttons = [
        [InlineKeyboardButton(opt, callback_data=opt[:60])] for opt in q["options"]
    ]
    # store full option text mapped by truncated callback_data key to survive Telegram's 64-byte limit
    context.user_data["quiz_option_map"] = {opt[:60]: opt for opt in q["options"]}

    await update.message.reply_text(
        f"What does *{q['word']}* mean?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chosen_key = query.data
    option_map = context.user_data.get("quiz_option_map", {})
    chosen = option_map.get(chosen_key, chosen_key)
    correct = context.user_data.get("quiz_correct_answer")
    word = context.user_data.get("quiz_word", "")

    user_id = update.effective_user.id
    is_correct = chosen == correct
    db.record_quiz_result(user_id, is_correct)

    if is_correct:
        result_text = f"✅ Correct! *{word}* means: {correct}"
    else:
        result_text = f"❌ Not quite. *{word}* actually means: {correct}"

    await query.edit_message_text(result_text, parse_mode="Markdown")


async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = db.get_progress(user.id)
    if not data:
        db.get_or_create_user(user.id, user.username or "", user.first_name or "")
        data = db.get_progress(user.id)

    accuracy = (
        round(100 * data["quiz_correct"] / data["quiz_total"], 1)
        if data["quiz_total"] else 0
    )
    text = (
        f"📊 Your progress:\n\n"
        f"Messages practiced: {data['messages_practiced']}\n"
        f"Quiz score: {data['quiz_correct']}/{data['quiz_total']} ({accuracy}%)\n"
        f"Current streak: {data['streak_days']} day(s)\n"
        f"Member since: {data['joined_at']}"
    )
    await update.message.reply_text(text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.username or "", user.first_name or "")
    db.touch_activity(user.id)
    db.increment_messages_practiced(user.id)

    user_message = update.message.text
    history = CONVO_HISTORY.setdefault(user.id, [])

    await update.message.chat.send_action("typing")
    reply = await get_coaching_reply(user_message, history)

    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    CONVO_HISTORY[user.id] = history[-10:]  # cap history length

    await update.message.reply_text(reply)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Update %s caused error %s", update, context.error)


def main():
    db.init_db()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("practice", practice))
    app.add_handler(CommandHandler("word", word_of_the_day))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("progress", progress))
    app.add_handler(CallbackQueryHandler(quiz_answer))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    logger.info("English Coach bot starting (polling mode)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
