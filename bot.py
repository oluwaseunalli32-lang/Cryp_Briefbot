import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# --- CoinGecko helpers ---
def get_coin_price(coin_id: str) -> dict:
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coin_id,
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return {}

def get_top_coins(limit: int = 5) -> list:
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": False,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return []

# --- Command handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Crypto Market Info Bot.\n\n"
        "I provide neutral price data and market information.\n"
        "**This is not financial advice.**\n\n"
        "Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**How to use this bot:**\n\n"
        "/price <coin> — Get price for a coin (e.g., /price bitcoin)\n"
        "/top — See top 5 coins by market cap\n"
        "/about — Learn about the data source\n\n"
        "**Disclaimer:** This bot provides information only, not financial advice."
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**About This Bot**\n\n"
        "Data is sourced from the CoinGecko public API.\n"
        "This bot is for informational purposes only.\n"
        "**It does not provide financial advice.**"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /price <coin_id>\nExample: /price bitcoin"
        )
        return
    coin = context.args[0].lower()
    data = get_coin_price(coin)
    if coin not in data:
        await update.message.reply_text(
            f"❌ Could not find data for '{coin}'.\n"
            "Use CoinGecko IDs (e.g., 'bitcoin', not 'BTC')."
        )
        return
    info = data[coin]
    price = info.get("usd", 0)
    change = info.get("usd_24h_change", 0)
    arrow = "📈" if change >= 0 else "📉"
    await update.message.reply_text(
        f"**{coin.capitalize()}**\n"
        f"Price: ${price:,.2f}\n"
        f"24h Change: {arrow} {change:+.2f}%"
    )

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coins = get_top_coins(5)
    if not coins:
        await update.message.reply_text("⚠️ Unable to fetch market data. Try again later.")
        return
    lines = ["**Top 5 Coins by Market Cap**\n"]
    for c in coins:
        change = c.get("price_change_percentage_24h", 0)
        arrow = "📈" if change >= 0 else "📉"
        lines.append(
            f"{arrow} **{c['symbol'].upper()}**: "
            f"${c['current_price']:,.2f} ({change:+.2f}%)"
        )
    await update.message.reply_text("\n".join(lines))

# --- App setup ---
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("about", about_command))
app.add_handler(CommandHandler("price", price))
app.add_handler(CommandHandler("top", top))

if __name__ == "__main__":
    print("Bot is running...")
    app.run_polling()
