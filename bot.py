import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

TOKEN = "8625202064:AAFYa88FW9Df-aKg-Cza55GzHu2iVPvvxjc"
ADMIN_ID = 2063744739

# DATABASE
db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

# USERS
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    username TEXT,
    password TEXT
)
""")

# KEYS
cursor.execute("""
CREATE TABLE IF NOT EXISTS keys(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT,
    key_text TEXT
)
""")

# BALANCE
cursor.execute("""
CREATE TABLE IF NOT EXISTS balance(
    username TEXT,
    amount REAL
)
""")

# USER PRICES
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_prices(
    username TEXT,
    product TEXT,
    price REAL
)
""")

db.commit()

# LOGIN SYSTEM
logged_users = {}

# DEFAULT PRICES
default_prices = {
    "flourite": 20,
    "gbox": 6.5,
    "esing": 6.5,
    "proxy": 3
}

# STOCK
def get_stock(product):

    cursor.execute(
        "SELECT COUNT(*) FROM keys WHERE product=?",
        (product,)
    )

    result = cursor.fetchone()

    return result[0]

# GET PRICE
def get_price(username, product):

    cursor.execute(
        "SELECT price FROM user_prices WHERE username=? AND product=?",
        (username, product)
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    return default_prices[product]

# GET BALANCE
def get_balance(username):

    cursor.execute(
        "SELECT amount FROM balance WHERE username=?",
        (username,)
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    return 0

# UPDATE BALANCE
def update_balance(username, amount):

    cursor.execute(
        "SELECT amount FROM balance WHERE username=?",
        (username,)
    )

    result = cursor.fetchone()

    if result:

        cursor.execute(
            "UPDATE balance SET amount=? WHERE username=?",
            (amount, username)
        )

    else:

        cursor.execute(
            "INSERT INTO balance VALUES (?, ?)",
            (username, amount)
        )

    db.commit()

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in logged_users:

        await update.message.reply_text(
            "🔐 LOGIN REQUIRED\n\nUse:\n/login username password"
        )

        return

    keyboard = [
        [InlineKeyboardButton("🛍 Buy keys", callback_data="shop")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")]
    ]

    await update.message.reply_text(
        "👋 Hello, welcome to panel!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# LOGIN
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 2:

        await update.message.reply_text(
            "Use: /login username password"
        )

        return

    username = context.args[0]
    password = context.args[1]

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = cursor.fetchone()

    if not user:

        await update.message.reply_text(
            "❌ Invalid username or password"
        )

        return

    logged_users[update.effective_user.id] = username

    keyboard = [
        [InlineKeyboardButton("🛍 Buy keys", callback_data="shop")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")]
    ]

    await update.message.reply_text(
        f"✅ Logged as {username}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# REGISTER
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 2:

        await update.message.reply_text(
            "Use: /register username password"
        )

        return

    username = context.args[0]
    password = context.args[1]

    cursor.execute(
        "INSERT INTO users VALUES (?, ?)",
        (username, password)
    )

    db.commit()

    update_balance(username, 0)

    await update.message.reply_text(
        f"✅ User {username} created"
    )

# ADD BALANCE
async def addbalance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 2:

        await update.message.reply_text(
            "Use: /addbalance username amount"
        )

        return

    username = context.args[0]
    amount = float(context.args[1])

    current = get_balance(username)

    new_balance = current + amount

    update_balance(username, new_balance)

    await update.message.reply_text(
        f"✅ Added ${amount} to {username}"
    )

# SET PRICE
async def setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 3:

        await update.message.reply_text(
            "Use: /setprice username product price"
        )

        return

    username = context.args[0]
    product = context.args[1].lower()
    price = float(context.args[2])

    cursor.execute(
        "DELETE FROM user_prices WHERE username=? AND product=?",
        (username, product)
    )

    cursor.execute(
        "INSERT INTO user_prices VALUES (?, ?, ?)",
        (username, product, price)
    )

    db.commit()

    await update.message.reply_text(
        f"✅ {username} now has {product} at ${price}"
    )

# ADD KEY
async def addkey(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:

        await update.message.reply_text(
            "Use: /addkey product key"
        )

        return

    product = context.args[0].lower()
    key_text = " ".join(context.args[1:])

    cursor.execute(
        "INSERT INTO keys (product, key_text) VALUES (?, ?)",
        (product, key_text)
    )

    db.commit()

    await update.message.reply_text(
        f"✅ Key added to {product}"
    )

# BUTTONS
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    username = logged_users.get(query.from_user.id)

    # BALANCE
    if query.data == "balance":

        await query.message.reply_text(
            f"💰 Balance: ${get_balance(username)}"
        )

    # SHOP
    elif query.data == "shop":

        keyboard = [
            [InlineKeyboardButton("💎 FLOURITE", callback_data="flourite")],
            [InlineKeyboardButton("📦 GBOX", callback_data="gbox")],
            [InlineKeyboardButton("🛡 ESING", callback_data="esing")],
            [InlineKeyboardButton("🌐 PROXY", callback_data="proxy")]
        ]

        await query.message.reply_text(
            "🛒 SELECT PRODUCT",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # PRODUCTS
    elif query.data in ["flourite", "gbox", "esing", "proxy"]:

        product = query.data

        keyboard = [
            [InlineKeyboardButton("🔑 Buy", callback_data=f"buy_{product}")],
            [InlineKeyboardButton("⬅ Go back", callback_data="shop")]
        ]

        await query.message.reply_text(
            f"🔑 {product.upper()} KEY\n"
            f"- Price: ${get_price(username, product)}\n"
            f"- Keys in stock: {get_stock(product)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # BUY
    elif query.data.startswith("buy_"):

        product = query.data.replace("buy_", "")

        price = get_price(username, product)

        balance = get_balance(username)

        if balance < price:

            await query.message.reply_text(
                "❌ Not enough balance"
            )

            return

        cursor.execute(
            "SELECT id, key_text FROM keys WHERE product=? LIMIT 1",
            (product,)
        )

        result = cursor.fetchone()

        if not result:

            await query.message.reply_text(
                "❌ OUT OF STOCK"
            )

            return

        key_id = result[0]
        key_text = result[1]

        cursor.execute(
            "DELETE FROM keys WHERE id=?",
            (key_id,)
        )

        db.commit()

        new_balance = balance - price

        update_balance(username, new_balance)

        await query.message.reply_text(
            f"✅ PURCHASE SUCCESS\n\n"
            f"🔑 KEY:\n{key_text}\n\n"
            f"💰 New Balance: ${new_balance}"
        )

# RUN
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("login", login))
app.add_handler(CommandHandler("register", register))
app.add_handler(CommandHandler("addbalance", addbalance))
app.add_handler(CommandHandler("setprice", setprice))
app.add_handler(CommandHandler("addkey", addkey))
app.add_handler(CallbackQueryHandler(button))

print("BOT ONLINE")
app.run_polling()