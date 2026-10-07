import os
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# ------------------------------------------------------------------
# CoinGecko helpers
# ------------------------------------------------------------------
def get_coin_price(coin_id: str) -> dict:
    """Fetch current price and 24h change for one coin."""
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
    """Fetch top N coins by market cap."""
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

# ------------------------------------------------------------------
# Command handlers
# ------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Crypto Market Info Bot.\n\n"
        "I provide neutral price data and market information.\n"
        "*This is not financial advice.*\n\n"
        "Use /help to see available commands.",
        parse_mode="Markdown",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*How to use this bot:*\n\n"
        "/price <coin> — Get price for a coin (e.g., /price bitcoin)\n"
        "/top — See top 5 coins by market cap\n"
        "/about — Learn about the data source\n\n"
        "*Disclaimer:* This bot provides information only, not financial advice.",
        parse_mode="Markdown",
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*About This Bot*\n\n"
        "Data is sourced from the CoinGecko public API.\n"
        "This bot is for informational purposes only.\n"
        "*It does not provide financial advice.*",
        parse_mode="Markdown",
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
    price_val = info.get("usd", 0)
    change = info.get("usd_24h_change", 0) or 0
    arrow = "📈" if change >= 0 else "📉"

    await update.message.reply_text(
        f"*{coin.capitalize()}*\n"
        f"Price: ${price_val:,.2f}\n"
        f"24h Change: {arrow} {change:+.2f}%",
        parse_mode="Markdown",
    )

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coins = get_top_coins(5)
    if not coins:
        await update.message.reply_text(
            "⚠️ Unable to fetch market data. Please try again later."
        )
        return

    lines = ["*Top 5 Coins by Market Cap*\n"]
    for c in coins:
        change = c.get("price_change_percentage_24h") or 0
        arrow = "📈" if change >= 0 else "📉"
        lines.append(
            f"{arrow} *{c['symbol'].upper()}*: "
            f"${c['current_price']:,.2f} ({change:+.2f}%)"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ------------------------------------------------------------------
# Application setup
# ------------------------------------------------------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("top", top))

    print("Bot is running...", flush=True)
    app.run_polling()

if __name__ == "__main__":
    # Defensive fix for Python 3.14's stricter asyncio behaviour.
    # On 3.10–3.12 this is a no-op; on 3.14 it ensures a loop exists.
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    main()
