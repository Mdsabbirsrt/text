import logging
import random
import stripe
import requests
from faker import Faker
import os
import string
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import telebot
from telebot import types

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Stripe configuration
stripe.api_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"
customer = stripe.Customer.create()
print(customer.last_response.request_id)

# Telegram bot configuration
API_TOKEN = '7819656172:AAEx160ouF8RmdDOdJO_XnRswUcSALu46to'
bot = telebot.TeleBot(API_TOKEN)
fake = Faker()

# User management data
user_credits = {}  # Store user credits
admin_id = 8143679178  # Admin user ID
registered_user_id = None  # Store only one user ID
free_checks_remaining = 10  # Free check limit
premium_users = set()  # Store premium user IDs
redeem_codes = {}  # Store redeem codes

def check_cards():
    # This is a mock function for checking cards; replace this with your actual logic
    # Sample data for demo purposes
    total_cards = 100
    charge_cards = 10
    live_cards = 0
    dead_cards = total_cards - charge_cards - live_cards
    return total_cards, charge_cards, live_cards, dead_cards


def start(update: Update, context: CallbackContext) -> None:
    """Sends a message with card statuses."""
    total, charge, live, dead = check_cards()
    
    # Calculate percentages
    total_percentage = 100
    charge_percentage = (charge / total) * 100
    live_percentage = (live / total) * 100
    dead_percentage = (dead / total) * 100

    # Formatting the message
    message = (
        f"\U0001F4CB *Total cards* ➞ {total} ({total_percentage:.2f}%)\n"
        f"\U0001F4B3 *Charge Cards* ➞ {charge} ({charge_percentage:.2f}%)\n"
        f"\U0001F4B5 *Live Cards* ➞ {live} ({live_percentage:.2f}%)\n"
        f"\u2620 *Dead Cards* ➞ {dead} ({dead_percentage:.2f}%)\n"
        f"\n\U0001F6AA *Status* ➞ Checked All \u2705\n\n"
        f"*Result* ➞ No Live Cards Found\n"
        f"\n*Checked by* ➞ @{update.effective_user.username if update.effective_user.username else 'unknown'}"
    )

    # Send the message
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='Markdown')

# Command to register a user manually
def register_user(update: Update, context: CallbackContext) -> None:
    global registered_user_id
    user_id = update.effective_user.id
    if registered_user_id is None:
        registered_user_id = user_id
        user_credits[user_id] = 15  # Register user with 15 credits
        context.bot.send_message(chat_id=update.effective_chat.id, text="You have successfully registered! You now have 15 credits for card checking.")
    elif registered_user_id == user_id:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are already registered and have 15 credits.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, only one user can register with this bot.")

def main() -> None:
    """Start the bot."""
    # Replace 'YOUR_TOKEN' with your actual bot token
    updater = Updater("YOUR_TOKEN")

    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("register", register_user))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
