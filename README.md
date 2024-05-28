# ChatGPT Telegram Bot
This project presents a Telegram bot integrated with OpenAI's ChatGPT, providing an interactive communication experience by delivering information and solutions based on predefined content. The bot is designed for educational courses, especially in the context of targeted advertising, offering users valuable recommendations and guides.

## Features
**Personalized Responses:** Utilizing the OpenAI neural network, the bot provides detailed and contextually relevant answers to user inquiries.

**Multilingual Support:** The bot supports responses in multiple languages, including Russian and Uzbek.

**Dynamic Content Update:** The bot automatically updates its knowledge base through Google Drive, ensuring that the information provided is always up-to-date.

**Access Management:** Access to the bot is controlled through a list of authorized users, updated via Google Docs.

**Automated File Distribution:** The bot can automatically send educational materials in PDF and image formats to users, following a set schedule.
## Setup
To get the bot up and running, you need to follow these steps:

### Telegram Bot Configuration:

- Create a new bot through __BotFather__ in Telegram and obtain a token.
- Specify the token and other necessary parameters in the configuration file.
### OpenAI Setup:

- Obtain an API key from the OpenAI website and configure parameters such as model name and temperature.
### Google Drive Integration:

- Configure access to Google Drive to manage the database and user list.
- Specify the IDs of the relevant files and folders on Google Drive.
### Dependency Installation:

- Install all the necessary dependencies listed in requirements.txt using `pip install -r requirements.txt`.
### Running the Bot:

- Launch the bot using the command `python main.py`.
## Usage
- After launching the bot, users can interact with it via Telegram, using predefined commands or sending text messages to get responses from ChatGPT.

## Developers
**Pestretsov Anton / @motleyton (telegram)** 
