import logging
import os
from dotenv import load_dotenv

from openai_helper import OpenAI
from telegram_bot import ChatGPTTelegramBot


def main():
    # Read .env file
    load_dotenv()

    # Setup logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    # Setup configurations
    model = os.environ.get('OPENAI_MODEL')
    openai_config = {
        'embeddings_folder_id': os.environ['EMBEDDINGS_FOLDER_ID'],
        'api_key': os.environ['OPENAI_API_KEY'],
        'temperature': float(os.environ.get('TEMPERATURE', 0)),
        'model': model,
        'service_account': os.environ['SERVICE_ACCOUNT_FILE'],
        'content_id_rus': os.environ['CONTENT_FOLDER_ID_RU'],
        'content_id_uz': os.environ['CONTENT_FOLDER_ID_UZ'],

    }

    telegram_config = {
        'users': os.environ.get('FILE_XLS_USERS'),
        'token': os.environ['TELEGRAM_BOT_TOKEN'],
        'bot_language': os.environ.get('BOT_LANGUAGE', 'ru'),
        'embeddings_folder_id': os.environ['EMBEDDINGS_FOLDER_ID'],
        'content_id_rus': os.environ['CONTENT_FOLDER_ID_RU'],
        'content_id_uz': os.environ['CONTENT_FOLDER_ID_UZ'],
        'service_account': os.environ['SERVICE_ACCOUNT_FILE'],
        'stickers_ids': os.environ['STICKERS_IDS'],
        'model_ft': os.environ.get('MODEL_FT'),
        'checklists_folder_jpg_rus': os.environ.get('CHECKLISTS_FOLDER_JPG_RUS'),
        'checklists_folder_jpg_uz': os.environ.get('CHECKLISTS_FOLDER_JPG_UZ'),
        'checklists_folder_pdf_rus': os.environ.get('CHECKLISTS_FOLDER_PDF_RUS'),
        'checklists_folder_pdf_uz': os.environ.get('CHECKLISTS_FOLDER_PDF_UZ'),
        'checklists_file_id_text_rus': os.environ.get('CHECKLISTS_FILE_ID_TEXT_RUS'),
        'checklists_file_id_text_uz': os.environ.get('CHECKLISTS_FILE_ID_TEXT_UZ'),

    }

    # Setup and run ChatGPT and Telegram bot
    openai = OpenAI(config=openai_config)
    telegram_bot = ChatGPTTelegramBot(config=telegram_config, openai=openai)
    telegram_bot.run()


if __name__ == '__main__':
    main()