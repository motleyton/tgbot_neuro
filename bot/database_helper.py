import json

from langchain_community.document_loaders import GoogleDriveLoader
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
import openai
from langchain_community.vectorstores.faiss import FAISS
import logging
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, config: dict):
        self.embeddings_folder_id = config['embeddings_folder_id']
        self.service_account = config['service_account']
        with open(self.service_account, 'r') as file:
            service_account_info = json.load(file)

        self.creds = Credentials.from_service_account_info(service_account_info)
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.language_file_ids = {
            'ru': config['content_id_rus'],
            'uz': config['content_id_uz']
        }
        self.range_name = "Sheet1!A1:C"

    def open_database(self):
        try:
            loader = GoogleDriveLoader(
                folder_id=self.embeddings_folder_id,
                service_account_key=self.service_account)

            docs = loader.load()
            texts = []
            for doc in docs:
                headers_to_split_on = [("#", "Header 1"), ("##", "Header 2")]
                markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
                markdown_splits = markdown_splitter.split_text(doc.page_content)

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=0, separators=[" ", ",", "\n"])
                split_docs = text_splitter.split_documents(markdown_splits)
                texts.extend(split_docs)

            embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)
            db = FAISS.from_documents(texts, embeddings)
            db.as_retriever()
            db.save_local('faiss_index')

            return db
        except Exception as e:
            logger.exception("Произошла ошибка при обновлении базы данных: %s", e)
            raise

    def get_course_content(self, language='ru'):
        file_id = self.language_file_ids.get(language)
        if not file_id:
            logger.error(f"Не найден ID файла для языка: {language}")
            return "Содержимое курса не найдено."

        try:
            loader = GoogleDriveLoader(document_ids=[file_id], service_account_key=self.service_account)
            docs = loader.load()
            if docs:
                return docs[0].page_content
            else:
                return "Содержимое файла не найдено или пусто."
        except Exception as e:
            logger.exception(f"Произошла ошибка при загрузке содержимого курса для языка {language}: {e}")
            return "Ошибка при получении содержимого курса."

    def list_files_in_folder(self, service, checklists_folder_id):
        try:
            results = service.files().list(
                q=f"'{checklists_folder_id}' in parents and trashed=false",
                pageSize=100,
                fields="nextPageToken, files(id, name)"
            ).execute()
            return results.get('files', [])
        except Exception as e:
            logger.exception(f"An error occurred while listing files in folder: {e}")
            return []

    def get_usernames_and_counters(self, file_id_users):
        try:
            # Имя листа и диапазон для чтения, например 'Sheet1' и весь лист
            result = self.service.spreadsheets().values().get(
                spreadsheetId=file_id_users,
                range=self.range_name
            ).execute()
            rows = result.get('values', [])
            if not rows or len(rows) < 1:
                return {}

            # Получаем индексы столбцов по их названиям из первой строки
            headers = rows[0]
            username_index = headers.index('username') if 'username' in headers else None
            counter_index = headers.index('counter') if 'counter' in headers else None
            if username_index is None or counter_index is None:
                logger.error("Не найдены необходимые столбцы: 'username' или 'counter'. Проверьте заголовки столбцов.")
                return {}

            data = {}
            # Обрабатываем все строки начиная со второй
            for i, row in enumerate(rows[1:], start=2):  # Начинаем с 2, так как rows[1] это данные после заголовков
                if len(row) > username_index:
                    username = row[username_index].strip()
                    counter = int(row[counter_index].strip()) if len(row) > counter_index and row[
                        counter_index].strip().isdigit() else 1
                    if username:
                        data[username] = (counter, i)  # Сохраняем счетчик и номер строки
            return data

        except Exception as e:
            logger.exception(f"Произошла ошибка при загрузке данных: {e}")
            return {}

    def update_counter(self, file_id_users, username, new_counter, row_number):
        try:
            range_to_update = f"Sheet1!C{row_number}"  # Предполагаем, что счетчик в столбце C
            value_range_body = {
                "values": [[str(new_counter)]],
                "majorDimension": "ROWS"
            }
            self.service.spreadsheets().values().update(
                spreadsheetId=file_id_users,
                range=range_to_update,
                valueInputOption="USER_ENTERED",
                body=value_range_body
            ).execute()
        except Exception as e:
            logger.exception(f"Ошибка при обновлении счетчика для пользователя {username}: {e}")
