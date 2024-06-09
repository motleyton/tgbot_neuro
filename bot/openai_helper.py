import logging
import os
from typing import Dict

import openai
import json

from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from database_helper import Database


# Load translations

translations_file_path = os.path.join('/home/bmf/Desktop/freelance/tgbot_neuro/translations.json')
with open(translations_file_path, 'r', encoding='utf-8') as f:
    translations = json.load(f)


def localized_text(key, bot_language):
    """
    Return translated text for a key in specified bot_language.
    Keys and translations can be found in the translations.json.
    """
    try:
        return translations[bot_language][key]
    except KeyError:
        logging.warning(f"No translation available for bot_language code '{bot_language}' and key '{key}'")
        if key in translations['ru']:
            return translations['ru'][key]
        logging.warning(f"No english definition found for key '{key}' in translations.json")
        return key


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OpenAI:
    """
    A class to interact with OpenAI's API, specifically for generating text responses
    based on the provided course content.

    Attributes:
        config (dict): Configuration dictionary containing API key, model, and other settings.
        model_name (str): Name of the model to use for generating responses.
        db_instance (Database): An instance of the Database class for accessing course content.
        db: Database object initialized from the db_instance.
        temperature (float): Sampling temperature for the model's response generation.
    """

    def __init__(self, config: Dict[str, any]):
        """
        Initializes the OpenAI class with necessary configurations.

        Args:
            config (Dict[str, any]): A configuration dictionary containing necessary keys like API key, model, etc.
        """

        openai.api_key = config['api_key']
        self.config = config
        self.model_name = config['model']
        self.db_instance = Database(config)
        self.db = self.db_instance.open_database()
        self.temperature = config['temperature']

    def initialize_chat(self):
        """
        Initializes a chat instance using the OpenAI's model, setting up with the predefined template.

        Returns:
            An instance of RetrievalQA chain, ready to be used for generating responses based on the course content.
        """

        llm = ChatOpenAI(
            temperature=self.temperature,
            openai_api_key=openai.api_key,
            model_name=self.model_name,
        )
        template = '''
            Вы — нейроконсультант на курсе по таргетированной рекламе. Ваша задача — предоставлять информацию, строго основываясь на предоставленном курсовом контенте. 
            Не добавляйте информацию от себя, не используйте данные из внешних источников и не ссылайтесь на исходные документы, не связанные с курсом.
            Ваши ответы должны быть уважительными, точными и полностью соответствовать контексту запроса пользователя. 
            При необходимости укажите на конкретный урок или раздел курса, который может помочь пользователю получить дополнительную информацию, и предложите дополнительные советы или 
            контекст, которые могут улучшить понимание материала.
        

            {context}

            Вопрос: {question}
            СТРОГО! Отвечай на вопрос на том же языке, на каком задан вопрос!!!.
            Формулируйте ответ, используя уважительное обращение и предоставляя конкретные ссылки на материалы курса. 
            Добавьте полезные советы или рекомендации, которые могут способствовать более глубокому пониманию темы.
            Не повторяй вопрос. 
            Не начинай ответ со слов "Ответ:" или "Нейроконсультант:"
            В случае, если соответствующая информация отсутствует или запрос не может быть однозначно интерпретирован на основе доступных данных, верните ответ: "Извините, но в материалах курса нет информации по вашему запросу."

        '''

        prompt = PromptTemplate(
            template=template, input_variables=["question", "context"]
        )
        chain_type_kwargs = {"prompt": prompt, 'verbose': False}

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.db.as_retriever(),
            chain_type_kwargs=chain_type_kwargs
        )
        return qa_chain