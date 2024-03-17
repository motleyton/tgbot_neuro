from langchain_community.document_loaders import GoogleDriveLoader
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
import openai
from langchain_community.vectorstores.faiss import FAISS
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, config: dict):
        self.embeddings_folder_id = config['embeddings_folder_id']
        self.service_account = config['service_account']
        self.language_file_ids = {
            'ru': config['content_id_rus'],
            'uz': config['content_id_uz']
        }

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

    def get_usernames(self, file_id_users):
        try:
            loader = GoogleDriveLoader(document_ids=[file_id_users], service_account_key=self.service_account)
            docs = loader.load()

            if docs:
                usernames = docs[0].page_content.splitlines()  # Предполагается, что каждый юзернейм на новой строке
                return [username.strip().replace('\ufeff', '') for username in usernames]
            else:
                return []
        except Exception as e:
            logger.exception(f"Произошла ошибка при загрузке списка пользователей: {e}")
            return []

