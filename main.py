import os
import logging
import openai
from dotenv import load_dotenv  # Import the function
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
load_dotenv()  # Load variables from your .env file

# This code now works everywhere: it reads from .env locally, 
# and from Render's environment variables when deployed.
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# The rest of your code remains exactly the same...

SYSTEM_PROMPT = "You are a helpful AI assistant. Always provide a response. If you cannot answer a question directly due to safety reasons or lack of information, you must explain that you cannot answer and state the reason why. Do not provide an empty response."

MODELS = [
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-7b-it:free",
    "nousresearch/nous-hermes-2-mixtral-8x7b-dpo:free",
    "openchat/openchat-7b:free",
    "huggingfaceh4/zephyr-7b-beta:free",
    "openrouter/cinematika-7b:free",
    "cognitivecomputations/dolphin-mixtral-8x7b:free",
    "gryphe/gryphe-mistral-7b-v2:free",
    "undi95/toppy-m-7b:free",
    "rwkv/rwkv-5-world-3b:free"
]

client = openai.OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENROUTER_API_KEY,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hello! I am a resilient AI assistant. I will try multiple AI models to always get you an answer. Ask me anything!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.effective_chat.id
    response_text = ""

    await context.bot.send_chat_action(chat_id=chat_id, action='typing')

    try:
        for model_name in MODELS:
            logging.info(f"Attempting to get response from model: {model_name}")
            try:
                completion = client.chat.completions.create(
                  model=model_name,
                  messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                  ],
                )
                
                response_text = completion.choices[0].message.content

                if response_text and response_text.strip():
                    logging.info(f"Successfully got response from {model_name}")
                    break
                else:
                    logging.warning(f"Model {model_name} returned an empty response. Trying next model.")
            
            except Exception as model_error:
                logging.error(f"Error with model {model_name}: {model_error}. Trying next model.")
                continue

        if response_text and response_text.strip():
            await context.bot.send_message(chat_id=chat_id, text=response_text)
        else:
            logging.error("All models failed to provide a valid response.")
            await context.bot.send_message(
                chat_id=chat_id,
                text="Sorry, all available AI models failed to provide a response. Please try again later."
            )

    except Exception as e:
        logging.error(f"A critical error occurred: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, I encountered a critical error."
        )

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Ultra-resilient bot is running...")
    application.run_polling()