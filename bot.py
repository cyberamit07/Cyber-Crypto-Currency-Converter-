import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import requests
import re
import time
import logging
import telebot

# ============= CONFIGURATION =============
TOKEN = "YOUR_BOT_TOKEN_HERE"  # Apna token daalein

# ⭐ Telegram Stars Price (1 Star = 1.3 INR)
STAR_RATE_INR = 1.3  # 1 Star = 1.3 Indian Rupees

FOOTER = "━━━━━━━━━━━━━━━━━━\nMade by @cyber_amit"

# ============= LOGGING =============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============= CONVERTER CLASS =============
class CryptoConverter:
    def __init__(self):
        self.prices = {}
        self.last_update = 0
        self.cache_duration = 60
        self.usd_to_inr = 0
        self.star_rate_usd = 0
    
    def get_live_prices(self):
        current_time = time.time()
        
        if self.prices and (current_time - self.last_update) < self.cache_duration:
            return self.prices
        
        try:
            logger.info("Fetching live prices...")
            
            # CoinGecko API - TON Price
            crypto_url = "https://api.coingecko.com/api/v3/simple/price"
            params = {'ids': 'the-open-network,tether', 'vs_currencies': 'usd'}
            response = requests.get(crypto_url, params=params, timeout=10)
            crypto_data = response.json()
            ton_price = crypto_data.get('the-open-network', {}).get('usd', 0)
            
            # ExchangeRate API - USD to INR
            inr_url = "https://api.exchangerate-api.com/v4/latest/USD"
            inr_response = requests.get(inr_url, timeout=10)
            inr_data = inr_response.json()
            self.usd_to_inr = inr_data.get('rates', {}).get('INR', 0)
            
            # Calculate Star rate in USD
            # 1 Star = 1.3 INR
            # 1 USD = usd_to_inr INR
            # 1 Star = 1.3 / usd_to_inr USD
            if self.usd_to_inr > 0:
                self.star_rate_usd = STAR_RATE_INR / self.usd_to_inr
            else:
                self.star_rate_usd = 0.01349  # Default fallback
            
            self.prices = {
                'TON': ton_price,
                'USDT': 1.0,
                'INR': 1 / self.usd_to_inr if self.usd_to_inr > 0 else 0,
                'STAR': self.star_rate_usd  # Star rate in USD
            }
            
            self.last_update = current_time
            
            logger.info(f"USD to INR: ₹{self.usd_to_inr}")
            logger.info(f"1 Star = ₹{STAR_RATE_INR} = ${self.star_rate_usd:.6f}")
            logger.info(f"Prices: {self.prices}")
            
            return self.prices
            
        except Exception as e:
            logger.error(f"API Error: {e}")
            if self.prices:
                return self.prices
            raise Exception("API failed")
    
    def get_all_conversions(self, amount, currency):
        """Convert amount to all currencies"""
        prices = self.get_live_prices()
        currency = currency.upper()
        
        logger.info(f"Converting: {amount} {currency}")
        logger.info(f"Current USD to INR: ₹{self.usd_to_inr}")
        logger.info(f"Star rate in USD: ${self.star_rate_usd:.6f}")
        
        # Step 1: Convert to USD first
        if currency == 'TON':
            usd_value = amount * prices['TON']
        elif currency == 'USDT':
            usd_value = amount * prices['USDT']
        elif currency == 'INR':
            usd_value = amount * prices['INR']
        elif currency == 'STAR':
            # Stars to USD: Stars * Star rate in USD
            usd_value = amount * prices['STAR']
        else:
            usd_value = amount
        
        logger.info(f"USD Value: ${usd_value:.6f}")
        
        # Step 2: Convert USD to all currencies
        results = {}
        
        # TON
        if prices['TON'] > 0:
            results['TON'] = usd_value / prices['TON']
        else:
            results['TON'] = 0
        
        # USDT
        if prices['USDT'] > 0:
            results['USDT'] = usd_value / prices['USDT']
        else:
            results['USDT'] = 0
        
        # INR
        if prices['INR'] > 0:
            results['INR'] = usd_value / prices['INR']
        else:
            results['INR'] = 0
        
        # STARS - Using fixed INR rate
        # 1 Star = 1.3 INR
        if self.usd_to_inr > 0:
            # Convert USD to INR then to Stars
            inr_value = usd_value * self.usd_to_inr
            results['STAR'] = inr_value / STAR_RATE_INR
        else:
            results['STAR'] = 0
        
        logger.info(f"Results: {results}")
        return results

converter = CryptoConverter()

# ============= BOT =============
bot = telebot.TeleBot(TOKEN)

def parse_input(text):
    """Parse user input - amount and currency"""
    text = text.lower().strip()
    logger.info(f"Parsing: {text}")
    
    # TON - t, ton
    match = re.match(r'^(\d+(?:\.\d+)?)\s*(?:ton|t)$', text)
    if match:
        return float(match.group(1)), 'TON'
    
    # USDT - u, usdt
    match = re.match(r'^(\d+(?:\.\d+)?)\s*(?:usdt|u)$', text)
    if match:
        return float(match.group(1)), 'USDT'
    
    # INR - i, inr, ₹
    match = re.match(r'^(\d+(?:\.\d+)?)\s*(?:inr|i)$', text)
    if match:
        return float(match.group(1)), 'INR'
    
    match = re.match(r'^₹\s*(\d+(?:\.\d+)?)$', text)
    if match:
        return float(match.group(1)), 'INR'
    
    match = re.match(r'^(\d+(?:\.\d+)?)\s*₹$', text)
    if match:
        return float(match.group(1)), 'INR'
    
    # STARS - s, star, stars, ⭐
    match = re.match(r'^(\d+(?:\.\d+)?)\s*(?:star|stars|s)$', text)
    if match:
        return float(match.group(1)), 'STAR'
    
    match = re.match(r'^⭐\s*(\d+(?:\.\d+)?)$', text)
    if match:
        return float(match.group(1)), 'STAR'
    
    match = re.match(r'^(\d+(?:\.\d+)?)\s*⭐$', text)
    if match:
        return float(match.group(1)), 'STAR'
    
    return None, None

def is_valid_input(text):
    """Strict validation for input format"""
    text = text.lower().strip()
    
    # List of valid patterns
    valid_patterns = [
        r'^\d+(?:\.\d+)?\s*ton$',
        r'^\d+(?:\.\d+)?\s*t$',
        r'^\d+(?:\.\d+)?\s*usdt$',
        r'^\d+(?:\.\d+)?\s*u$',
        r'^\d+(?:\.\d+)?\s*inr$',
        r'^\d+(?:\.\d+)?\s*i$',
        r'^₹\s*\d+(?:\.\d+)?$',
        r'^\d+(?:\.\d+)?\s*₹$',
        r'^\d+(?:\.\d+)?\s*star$',
        r'^\d+(?:\.\d+)?\s*stars$',
        r'^\d+(?:\.\d+)?\s*s$',
        r'^⭐\s*\d+(?:\.\d+)?$',
        r'^\d+(?:\.\d+)?\s*⭐$',
    ]
    
    for pattern in valid_patterns:
        if re.match(pattern, text):
            return True
    return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = f"""🔄 Crypto Converter Bot

Convert between TON, USDT, INR, and Telegram Stars!

How to use:
• 2ton or 2t - 2 TON
• 5usdt or 5u - 5 USDT
• 500inr or 500i - 500 INR
• 100star or 100s - 100 Stars

Examples:
1t  2ton  5u  100usdt  500i  250s

⭐ 1 Star = ₹{STAR_RATE_INR}

Use /help for more info."""
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = f"""📚 Help & Commands

Supported Formats:
TON: 1t, 2ton
USDT: 5u, 10usdt
INR: 500i, ₹500, 500₹
Stars: 100⭐, 250s, 500star

Commands:
/start - Welcome
/help - This help
/status - Check prices

⭐ Star Rate: 1 Star = ₹{STAR_RATE_INR}

Example:
2ton → Shows all conversions"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['status'])
def send_status(message):
    try:
        prices = converter.get_live_prices()
        
        # Calculate Star rate in INR
        usd_to_inr = converter.usd_to_inr
        star_in_inr = STAR_RATE_INR
        
        status_text = f"""✅ Bot Status

🟢 Online

Current Prices:
💎 TON: ${prices.get('TON', 0):.4f}
💵 USDT: ${prices.get('USDT', 0):.4f}
🇮🇳 USD to INR: ₹{usd_to_inr:.2f}
⭐ Stars: ₹{star_in_inr:.2f} each
⭐ Stars: ${prices.get('STAR', 0):.6f} each

⚡ 1 Star = ₹{STAR_RATE_INR}"""
        bot.reply_to(message, status_text)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_conversion(message):
    try:
        # Ignore if message starts with / (commands)
        if message.text.startswith('/'):
            return
        
        text = message.text.strip()
        
        # CHECK: If input is NOT valid, simply return (do nothing)
        if not is_valid_input(text):
            logger.info(f"Ignoring invalid input: {text}")
            return  # ← Yahan pe bot kuch reply nahi karega
        
        # Parse input
        amount, currency = parse_input(text)
        
        if amount is None or currency is None:
            logger.info(f"Ignoring invalid input (parse failed): {text}")
            return  # ← Yahan pe bhi bot kuch reply nahi karega
        
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Get conversions
        conversions = converter.get_all_conversions(amount, currency)
        
        # Format result with proper decimal places
        result = f"💎 TON : {conversions.get('TON', 0):.4f}\n"
        result += f"💵 USDT : {conversions.get('USDT', 0):.4f}\n"
        result += f"🇮🇳 INR : {conversions.get('INR', 0):.2f}\n"
        result += f"⭐ STARS : {conversions.get('STAR', 0):.2f}\n"
        result += f"\n📊 {amount} {currency} → All Currencies"
        result += f"\n⭐ 1 Star = ₹{STAR_RATE_INR}"
        result += f"\n{FOOTER}"
        
        bot.reply_to(message, result)
        logger.info(f"Conversion sent: {amount} {currency} → {conversions}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        # Error bhi silent karo, kuch reply na karo
        # bot.reply_to(message, f"❌ Error: {str(e)}")

def main():
    try:
        print("=" * 50)
        print("🤖 Crypto Converter Bot Starting...")
        print("=" * 50)
        
        # Test API
        try:
            prices = converter.get_live_prices()
            usd_to_inr = converter.usd_to_inr
            star_in_inr = STAR_RATE_INR
            star_in_usd = converter.star_rate_usd
            
            print("✅ API Connected!")
            print(f"💎 TON: ${prices.get('TON', 0):.4f}")
            print(f"💵 USDT: ${prices.get('USDT', 0):.4f}")
            print(f"🇮🇳 USD to INR: ₹{usd_to_inr:.2f}")
            print(f"⭐ 1 Star = ₹{star_in_inr:.2f} = ${star_in_usd:.6f}")
        except Exception as e:
            print(f"⚠️ API Warning: {e}")
        
        print("\n" + "=" * 50)
        print("✅ Bot is running...")
        print("Press Ctrl+C to stop")
        print("=" * 50 + "\n")
        
        bot.infinity_polling()
        
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
