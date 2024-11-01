import telebot
from telebot import types
import random
import stripe
import requests
from faker import Faker
import os
import string

stripe.api_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"

customer = stripe.Customer.create()
print(customer.last_response.request_id)

API_TOKEN = '7819656172:AAEx160ouF8RmdDOdJO_XnRswUcSALu46to'
bot = telebot.TeleBot(API_TOKEN)
fake = Faker()

user_credits = {}  # Store user credits
admin_id = 8143679178  # Admin user ID
registered_user_id = None  # Store only one user ID
free_checks_remaining = 10  # Free check limit
premium_users = set()  # Store premium user IDs
redeem_codes = {}  # Store redeem codes

# Command to start the bot
@bot.message_handler(commands=['start'])
def send_welcome(message):
    global registered_user_id
    if registered_user_id is None:
        registered_user_id = message.from_user.id
        user_credits[message.from_user.id] = 15  # Register user with 15 credits
        bot.reply_to(message, "Welcome! You've received 15 free credits for card checking! Send me a list of cards, and I'll check them for you!")
    elif registered_user_id == message.from_user.id:
        bot.reply_to(message, "Welcome back! You already have 15 credits.")
    else:
        bot.reply_to(message, "Sorry, only one user can register with this bot.")

# Command for admin to show user details
@bot.message_handler(commands=['admin_show_users'])
def show_user_details(message):
    user_id = message.from_user.id
    if user_id != admin_id:
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    if not user_credits:
        bot.reply_to(message, "No users registered yet.")
        return

    user_details = "User Details:\n"
    for user, credits in user_credits.items():
        premium_status = "Premium User" if user in premium_users else "Standard User"
        user_details += f"User ID: {user}, Credits: {credits}, Status: {premium_status}\n"
    
    bot.reply_to(message, user_details)

# Command to show total number of users
@bot.message_handler(commands=['total_users'])
def total_users(message):
    user_id = message.from_user.id
    if user_id != admin_id:
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    total_users_count = len(user_credits)
    bot.reply_to(message, f"Total number of users: {total_users_count}")

# Command to ban a user
@bot.message_handler(commands=['ban'])
def ban_user(message):
    user_id = message.from_user.id
    if user_id != admin_id:
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    try:
        user_to_ban = int(message.text.split(' ')[1])  # Extract user ID to ban after the /ban command
    except (IndexError, ValueError):
        bot.reply_to(message, "Please provide a valid user ID to ban in the format: /ban user_id")
        return

    if user_to_ban in user_credits:
        del user_credits[user_to_ban]  # Remove user from credits dictionary
        if user_to_ban in premium_users:
            premium_users.remove(user_to_ban)  # Remove from premium users if applicable
        if user_to_ban == registered_user_id:
            global registered_user_id
            registered_user_id = None  # Allow a new user to register
        bot.reply_to(message, f"User ID {user_to_ban} has been banned successfully.")
    else:
        bot.reply_to(message, "User ID not found.")

# Command to redeem credits
@bot.message_handler(commands=['redeem'])
def redeem_credits(message):
    user_id = message.from_user.id
    if user_id != registered_user_id:
        return

    try:
        code = message.text.split(' ')[1]  # Extract the redeem code after the /redeem command
    except IndexError:
        bot.reply_to(message, "Please provide a redeem code after the /redeem command in the format: /redeem code")
        return

    if code in redeem_codes and not redeem_codes[code]['used']:
        user_credits[user_id] += redeem_codes[code]['credits']
        redeem_codes[code]['used'] = True
        bot.reply_to(message, f"You have successfully redeemed {redeem_codes[code]['credits']} credits! You now have {user_credits[user_id]} credits.")
    else:
        bot.reply_to(message, "Invalid or already used redeem code.")

# Command to add premium user
@bot.message_handler(commands=['premium'])
def add_premium_user(message):
    user_id = message.from_user.id
    if user_id != registered_user_id:
        return

    premium_users.add(user_id)
    user_credits[user_id] = 1000  # Set 1000 credits for premium users
    bot.reply_to(message, "Congratulations! You are now a premium user with 1000 credits.")

# Command to register a user manually
@bot.message_handler(commands=['register'])
def register_user(message):
    global registered_user_id
    if registered_user_id is None:
        registered_user_id = message.from_user.id
        user_credits[message.from_user.id] = 15  # Register user with 15 credits
        bot.reply_to(message, "You have successfully registered! You now have 15 credits for card checking.")
    elif registered_user_id == message.from_user.id:
        bot.reply_to(message, "You are already registered and have 15 credits.")
    else:
        bot.reply_to(message, "Sorry, only one user can register with this bot.")

# Command to create a redeem code (admin only)
@bot.message_handler(commands=['mack'])
def create_redeem_code(message):
    user_id = message.from_user.id
    if user_id != admin_id:
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    # Generate a random redeem code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    credits = 10  # Set default credits for the redeem code
    redeem_codes[code] = {'credits': credits, 'used': False}
    bot.reply_to(message, f"Redeem code created: {code} (Credits: {credits})")

# Command to set a new Stripe secret key
@bot.message_handler(commands=['sk'])
def set_stripe_key(message):
    user_id = message.from_user.id
    if user_id != admin_id:
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    try:
        new_sk_key = message.text.split(' ')[1]  # Extract the new secret key after the /sk command
    except IndexError:
        bot.reply_to(message, "Please provide a new Stripe secret key after the /sk command in the format: /sk sk_test_xxx")
        return

    stripe.api_key = new_sk_key
    bot.reply_to(message, "Stripe secret key has been updated successfully.")

# Command to start checking a specific card
@bot.message_handler(commands=['chk'])
def start_single_card_check(message):
    global free_checks_remaining
    user_id = message.from_user.id
    if user_id != registered_user_id:
        return

    if user_credits.get(user_id, 0) < 2 and free_checks_remaining <= 0:
        bot.reply_to(message, "You don't have enough credits. Each card check costs 2 credits. Please register or invite friends to get more credits.")
        return

    try:
        card_details = message.text.split(' ')[1]  # Extract the card details after the /chk command
    except IndexError:
        bot.reply_to(message, "Please provide card details after the /chk command in the format: /chk card_number|exp_month|exp_year|cvc")
        return
    
    bot.reply_to(message, f"Starting to check card: {card_details}...")

    # Deduct credits or use free checks
    if user_id in premium_users:
        pass  # Premium users do not lose credits
    elif free_checks_remaining > 0:
        free_checks_remaining -= 1
    else:
        user_credits[user_id] -= 2

    # Simulate checking the card (this is a random simulation for demonstration purposes)
    if not validate_card_format(card_details):
        result = f"Card: {card_details} ➜ Your card number is incorrect"
    else:
        try:
            # Split card details
            card_number, exp_month, exp_year, cvc = card_details.split('|')
            # Create a payment method using Stripe API
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": card_number,
                    "exp_month": int(exp_month),
                    "exp_year": int(exp_year),
                    "cvc": cvc,
                },
            )
            # Charge the card $1
            payment_intent = stripe.PaymentIntent.create(
                amount=100,  # $1.00 in cents
                currency="usd",
                payment_method=payment_method.id,
                confirm=True,
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            )
            charges = payment_intent.last_response.data
            card_info = get_card_info(card_number)
            if '"status": "succeeded"' in charges:
                status = "Approved ✅"
                resp = "Charged 1$🔥"
                save_approved_card(card_info, resp)
            elif '"cvc_check": "pass"' in charges:
                status = "LIVE ✅"
                resp = "CVV Live"
                save_approved_card(card_info, resp)
            elif "generic_decline" in charges:
                status = "Declined ❌"
                resp = "Generic Decline"
            elif "insufficient_funds" in charges:
                status = "LIVE ✅"
                resp = "Insufficient funds 💰"
                save_approved_card(card_info, resp)
            elif "fraudulent" in charges:
                status = "Declined ❌"
                resp = "Fraudulent"
            elif "do_not_honor" in charges:
                status = "Declined ❌"
                resp = "Do Not Honor"
            elif "authentication_required" in charges or "card_error_authentication_required" in charges:
                status = "LIVE ✅"
                resp = "3D Secured"
            else:
                status = "Declined ❌"
                resp = "Declined for an unknown reason"

            result = (
                f"Card: {card_details} ➜ {status} ({resp})\n"
                f"𝗜𝗻𝗳𝗼:\n"
                f"𝐈𝐬𝐬𝐮𝐞𝐫: {card_info.get('issuer', 'Unknown Issuer')}\n"
                f"𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {card_info.get('country', 'Unknown Country')}\n"
                f"🌍 𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {card_info.get('country_name', 'N/A')} {card_info.get('country_flag', 'N/A')}\n"
            )
        except stripe.error.CardError as e:
            # Handle decline error from Stripe
            markup = types.InlineKeyboardMarkup()
            decline_button = types.InlineKeyboardButton(text="Card Declined ❌", callback_data="card_declined")
            markup.add(decline_button)
            bot.reply_to(message, f"Card: {card_number} ➜ Declined ❌", reply_markup=markup)
            return
        except stripe.error.StripeError as e:
            # Handle other Stripe errors
            markup = types.InlineKeyboardMarkup()
            decline_button = types.InlineKeyboardButton(text="Card Declined ❌", callback_data="card_declined")
            markup.add(decline_button)
            bot.reply_to(message, f"Card: {card_number} ➜ Declined ❌", reply_markup=markup)
            return
        except Exception as e:
            # Handle any other exceptions
            result = f"Card: {card_details} ➜ An unexpected error occurred ❌ ({str(e)})"

    # Send the result back to the user
    if result:
        markup = types.InlineKeyboardMarkup()
        charge_button = types.InlineKeyboardButton(text="Total Charge: $1 ✅", callback_data="charge_success")
        decline_button = types.InlineKeyboardButton(text="Total Declined ❌", callback_data="card_declined")
        markup.add(charge_button, decline_button)
        bot.reply_to(message, result, reply_markup=markup)

# Command to start card checking with /chkk
@bot.message_handler(commands=['chkk'])
def start_card_check_live(message):
    global free_checks_remaining
    user_id = message.from_user.id
    if user_id != registered_user_id:
        return

    if user_credits.get(user_id, 0) < 2 and free_checks_remaining <= 0:
        bot.reply_to(message, "You don't have enough credits. Each card check costs 2 credits. Please register or invite friends to get more credits.")
        return

    # Simulate checking the card (this is a random simulation for demonstration purposes)
    live_card = random.choice([True, False])
    if live_card:
        # Extract card number to get card information
        card_number, exp_month, exp_year, cvc = card_details.split('|')
        card_info = get_card_info(card_number)
        issuer = card_info.get("issuer", "Unknown Issuer")
        country = card_info.get("country", "Unknown Country")

        result = (
            f"Card: {card_details} ➜ Card is Live ✅\n"
            f"𝗜𝗻𝗳𝗼:\n"
            f"𝐈𝐬𝐬𝐮𝐞𝐫: {issuer}\n"
            f"𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {country}\n"
            f"🌍 𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {card_info.get('country_name', 'N/A')} {card_info.get('country_flag', 'N/A')}\n"
        )
    else:
        result = None
        # Only show a Declined button
        markup = types.InlineKeyboardMarkup()
        decline_button = types.InlineKeyboardButton(text="Card Declined ❌", callback_data="card_declined")
        markup.add(decline_button)
        bot.reply_to(message, f"Card: {card_details} ➜ Declined ❌", reply_markup=markup)
        return

    # Send the result back to the user
    if result:
        markup = types.InlineKeyboardMarkup()
        live_button = types.InlineKeyboardButton(text="Card Live ✅", callback_data="card_live")
        decline_button = types.InlineKeyboardButton(text="Total Declined ❌", callback_data="card_declined")
        markup.add(live_button, decline_button)
        bot.reply_to(message, result, reply_markup=markup)

# Helper function to validate card format
def validate_card_format(card):
    parts = card.split('|')
    return len(parts) == 4 and all(part.isdigit() for part in parts[:3]) and len(parts[0]) == 16

# Helper function to get card information (mocked for now)
def get_card_info(card_number):
    return {
        "issuer": "Mock Bank",
        "country": "Mock Country",
        "country_name": "Mockland",
        "country_flag": "🌍"
    }

# Helper function to save approved card details (mocked for now)
def save_approved_card(card_info, response):
    # This function should save card details somewhere for reference
    print(f"Saving approved card: {card_info}, Response: {response}")

# Polling to keep the bot running
bot.polling()
