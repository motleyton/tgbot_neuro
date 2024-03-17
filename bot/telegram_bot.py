import logging
import random
from typing import Dict, Set
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, \
    filters, ContextTypes, CallbackContext, CallbackQueryHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database_helper import Database
from utils import error_handler
from openai_helper import localized_text, OpenAI
import fasttext
from file_sender import FileSender

class ChatGPTTelegramBot:
    """
    A Telegram bot integrated with OpenAI's GPT model and capable of sending automated files.

    Attributes:
        config (dict): Configuration dictionary containing necessary keys and tokens.
        openai (OpenAI): The OpenAI GPT instance for generating text responses.
        db (Database): Instance of the Database class for data retrieval and management.
        allowed_usernames (list): List of Telegram usernames allowed to interact with the bot.
        user_languages (dict): Dictionary to store users' language preferences.
        stickers_ids (str): Path to a file containing sticker IDs for the bot to send.
        bot (Bot): The Telegram Bot instance.
        file_sender (FileSender): An instance of FileSender for handling file-related operations.
        service (Resource): Google API service resource for accessing Drive API.
        active_users (set): A set of active user IDs that have interacted with the bot.
        counter (int): A counter used for iterating through files to send.
    """

    def __init__(self, config: Dict, openai: OpenAI):
        self.config = config
        self.openai = openai
        self.db = Database(config)
        self.file_id_users = config['users']
        self.allowed_usernames = self.db.get_usernames(self.file_id_users)
        self.user_languages: Dict[int, str] = {}
        self.stickers_ids = config['stickers_ids']
        self.model = fasttext.load_model('lid.176.bin')
        self.bot = telegram.Bot(token=config['token'])
        self.file_sender = FileSender()
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.service = self.file_sender.oauth(self.scopes, self.config['service_account'])
        self.checklists_folder_jpg_rus = config['checklists_folder_jpg_rus']
        self.checklists_folder_jpg_uz = config['checklists_folder_jpg_uz']
        self.checklists_folder_pdf_rus = config['checklists_folder_pdf_rus']
        self.checklists_folder_pdf_uz = config['checklists_folder_pdf_uz']
        self.checklists_file_id_text_rus = config['checklists_file_id_text_rus']
        self.checklists_file_id_text_uz = config['checklists_file_id_text_uz']
        self.active_users: Set[int] = set()
        self.counter = 1

    async def start(self, update: Update, context: CallbackContext) -> None:
        """
        Sends a welcome message and asks the user to select a language.

        Args:
            update (Update): The incoming update.
            context (CallbackContext): The context of the callback.
        """

        user_id = update.effective_user.id
        self.active_users.add(user_id)
        bot_language = self.config['bot_language']
        username = "@" + update.message.from_user.username if update.message.from_user.username else None
        disallowed = (
            localized_text('disallowed', bot_language))
        if username not in self.allowed_usernames:
            await update.message.reply_text(disallowed, disable_web_page_preview=True)
            return

        welcome_message = "Привет! Выберите язык / Salom! Tilni tanlang."
        keyboard = [
            [
                InlineKeyboardButton("Русский", callback_data='ru'),
                InlineKeyboardButton("Узбекский", callback_data='uz')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

    async def button(self, update: Update, context: CallbackContext) -> None:
        """
        Handles language selection buttons and updates user language preference.

        Args:
            update (Update): The incoming update.
            context (CallbackContext): The context of the callback.
        """

        query = update.callback_query
        await query.answer()
        language = query.data  # 'ru' или 'uz'
        user_id = update.effective_user.id

        # Сохраняем выбранный язык в словаре user_languages
        self.user_languages[user_id] = language
        welcome_message_rus = ''' 
        Вы выбрали русский язык. А теперь расскажем про возможности бота. 🧙‍♂️ Это ваш персональный нейро-тьютор. Ему можно задавать вопросы по урокам. Дополнительно бот будет дарить вам полезные памятки и ссылки. 🌸 Попробуйте сейчас спросить, что такое таргетированная реклама.
        '''

        welcome_message_uz = '''
        Siz rus tilini tanladingiz. Endi botning imkoniyatlari haqida gapiraylik. 🧙‍♂️ Bu sizning shaxsiy neyro-o’qituvchingiz. Unga darslar haqida savollar berishingiz mumkin. Bundan tashqari, bot sizga foydali eslatmalar va havolalar beradi. 🌸 Endi maqsadli reklama nima ekanligini soʻrab koʻring.
        '''

    # Отправляем подтверждающее сообщение на выбранном языке
        if language == 'ru':
            confirmation_message = welcome_message_rus
        elif language == 'uz':
            confirmation_message = welcome_message_uz
        await query.edit_message_text(text=confirmation_message)

        # Обновляем язык бота в конфигурации
        self.config['bot_language'] = language

    async def help(self, update: Update, context: CallbackContext) -> None:
        """
        Sends a help message to the user.

        Args:
            update (Update): The incoming update.
            context (CallbackContext): The context of the callback.
        """
        
        user_id = update.message.from_user.id
        username = "@" + update.message.from_user.username if update.message.from_user.username else None

        # Получаем язык пользователя; используем язык по умолчанию, если для пользователя не установлен язык
        user_language = self.user_languages.get(user_id, self.config.get('default_language', 'ru'))

        if username not in self.allowed_usernames:
            disallowed = localized_text('disallowed', user_language)
            await update.message.reply_text(disallowed, disable_web_page_preview=True)
            return

        help_texts = localized_text('help_text', user_language)
        help_message = "\n".join(help_texts)  # Объединяем все строки помощи в одно сообщение
        await update.message.reply_text(help_message, disable_web_page_preview=True)

    async def message_handler(self, update: Update, context: CallbackContext) -> None:
        """
        Handles incoming messages and responds accordingly.

        Args:
            update (Update): The incoming update.
            context (CallbackContext): The context of the callback.
        """

        user_id = update.message.from_user.id
        user_message = update.message.text
        user_language = self.user_languages.get(user_id, self.config.get('default_language', 'ru'))

        # Определение языка входящего сообщения с использованием FastText
        try:
            predictions = self.model.predict(user_message, k=1)  # k=1 возвращает самый вероятный язык
            detected_language = predictions[0][0].replace("__label__", "")
        except Exception as e:
            logging.error(f"Ошибка при определении языка: {e}")
            await update.message.reply_text("Ошибка при определении языка сообщения.")
            return

        # Проверка соответствия языка сообщения и выбранного пользователем языка
        if detected_language != user_language:
            error_message = "Пожалуйста, задавайте вопросы на русском языке." if user_language == 'ru' else "Iltimos, savollaringizni o'zbek tilida bering."
            await update.message.reply_text(error_message)
            return

        processing_message = "Пока ваш запрос обрабатывается, ловите котика" if user_language == 'ru' \
            else "Hozircha so’rovingiz ko’rib chiqilmoqda, mushukchani tuting"
        processing_message_id = await update.message.reply_text(processing_message)

        # Отправка случайного стикера
        try:
            with open(self.stickers_ids, 'r') as file:
                stickers = file.readlines()
                stickers = [line.strip() for line in stickers if line.strip()]
                sticker_file_id = random.choice(stickers)  # Выбор случайного file_id
        except Exception as e:
            logging.error(f"Ошибка при чтении файла стикеров: {e}")
            await update.message.reply_text("Произошла ошибка при обработке вашего запроса.")
            return

        await update.message.reply_sticker(sticker=sticker_file_id)

        qa_chain = self.openai.initialize_chat()
        response = qa_chain.run(user_message)
        await update.message.reply_text(response)

    async def course_content(self, update: Update, context: CallbackContext) -> None:
        """
        Sends the course content to the user.

        Args:
            update (Update): The incoming update.
            context (CallbackContext): The context of the callback.
        """

        user_id = update.effective_user.id
        user_language = self.user_languages.get(user_id, self.config.get('default_language', 'ru'))

        # Используйте ваш Database класс для получения текста курса
        content = self.db.get_course_content(language=user_language)
        await update.message.reply_text(content[:4096])  # Telegram имеет ограничение в 4096 символов на сообщение

    async def send_files_by_counter(self, service) -> None:
        """
        Sends files to users based on a counter which iterates through the files.

        Args:
            service: The Google Drive API service instance.
        """

        caption_text_dict = {}
        global counter
        for user_id in self.active_users:

            user_language = self.user_languages.get(user_id, self.config.get('default_language'))


            # Определение ID папок в зависимости от выбранного языка
            jpg_folder_id = self.checklists_folder_jpg_rus if user_language == 'ru' else self.checklists_folder_jpg_uz
            pdf_folder_id = self.checklists_folder_pdf_rus if user_language == 'ru' else self.checklists_folder_pdf_uz
            checklists_text = self.checklists_file_id_text_rus if user_language == 'ru' else self.checklists_file_id_text_uz
            # Получение файлов из папок
            jpg_files = self.db.list_files_in_folder(service, jpg_folder_id)
            pdf_files = self.db.list_files_in_folder(service, pdf_folder_id)
            try:
                # Загрузка и разбор текста
                text = await self.file_sender.download_file(service, checklists_text, is_google_doc=True)
                caption_text_dict = self.file_sender.extract_sections(text) if text else {}
            except Exception as e:
                print(f"Error downloading or parsing text: {e}")

            caption_text = caption_text_dict.get(str(self.counter), "Текст не найден")

            selected_files = [f for f in jpg_files + pdf_files if f['name'].startswith(str(self.counter))]

            for file in selected_files:
                file_stream = await self.file_sender.download_file(service, file['id'], is_google_doc=False)

                if file['name'].endswith('.jpg'):
                    file_stream.seek(0)
                    await self.bot.send_photo(chat_id=user_id, photo=file_stream, caption=caption_text)
                elif file['name'].endswith('.pdf'):
                    file_stream.seek(0)
                    await self.bot.send_document(chat_id=user_id, document=file_stream, filename=file['name'])

        if caption_text_dict:
            self.counter = (self.counter % len(caption_text_dict)) + 1
        else:
            self.counter += 1

    def start_scheduler(self) -> None:
        """
        Starts the APScheduler to periodically execute tasks.
        """

        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.send_files_by_counter, 'interval', seconds=20, args=[self.service])
        scheduler.start()

    def run(self) -> None:
        """
        Initiates the bot and starts polling for updates.
        """

        application = ApplicationBuilder() \
            .token(self.config['token']) \
            .concurrent_updates(True) \
            .build()

        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('help', self.help))
        application.add_handler(CommandHandler('course_content', self.course_content))
        application.add_handler(CallbackQueryHandler(self.button))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.message_handler))

        application.add_error_handler(error_handler)
        self.start_scheduler()

        application.run_polling()