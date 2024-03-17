import io
import re
from typing import Dict
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


class FileSender:
    """
    A utility class to handle file downloads and content extraction from Google Drive.

    Methods:
        oauth: Establishes a connection to the Google Drive API.
        download_file: Downloads a file from Google Drive.
        extract_sections: Extracts sections from a text based on a specific pattern.
    """

    def oauth(self, scopes: list, service_account_file: str):
        """
        Authenticate and create a Google Drive API service instance.

        Args:
            scopes (list): A list of strings representing the scopes (permissions) the service needs.
            service_account_file (str): Path to the service account credentials file.

        Returns:
            A Google Drive API service instance.
        """

        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=scopes)

        service = build('drive', 'v3', credentials=credentials)

        return service
    
    async def download_file(self, service, file_id: str, is_google_doc: bool = False) -> io.BytesIO:
        """
        Asynchronously downloads a file from Google Drive and returns its content.

        Args:
            service: Authenticated Google Drive service instance.
            file_id (str): The unique identifier for the file on Google Drive.
            is_google_doc (bool): True if the file is a Google Doc; False otherwise.

        Returns:
            A BytesIO object containing the file's content.
        """

        if is_google_doc:
            request = service.files().export_media(fileId=file_id, mimeType='text/plain')
        else:
            request = service.files().get_media(fileId=file_id)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        fh.seek(0)

        if is_google_doc:
            text_content = fh.read().decode('utf-8')
            return text_content
        else:
            return fh

    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        Extracts sections from a given text using a predefined pattern.

        Args:
            text (str): The text from which sections are to be extracted.

        Returns:
            A dictionary where the keys are section numbers and values are the corresponding section text.
        """

        pattern = r"(\d+)\)(.+?)(?=\d+\)|$)"
        sections = re.findall(pattern, text, re.DOTALL)
        return {section[0]: section[1].strip() for section in sections}