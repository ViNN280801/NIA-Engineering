# NIASupportBot

NIASupportBot is a Telegram bot designed to provide motivational phrases and other interactions through Telegram commands and buttons. This bot is built using Python and the `python-telegram-bot` library.

## Features

- **Start Command**: Initializes the bot and provides a custom keyboard with options.
- **Phrase Button**: Sends a random motivational phrase from a predefined list.
- **Image Button**: Placeholder for future implementation of sending images.
- **Logging**: Logs all interactions and messages to both the console and a log file.
- **User Details**: Captures and logs user details including ID, username, full name, and optional birth date or bio.

## Setup

### Prerequisites

- Python 3.7+
- Telegram Bot Token from [BotFather](https://t.me/BotFather)

### Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/yourusername/TelegramBot.git
    cd TelegramBot
    ```

2. **Create a virtual environment and activate it:**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up your bot token:**
    - Create a file named `bot_token.py` in the root directory and add your bot token:
    ```python
    BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
    ```

## Usage

### Running the Bot

To start the bot, run the following command:

```sh
python main.py
```

### Interacting with the Bot

* Start the Bot: Send /start to the bot. This will initialize the bot and display a custom keyboard with "Phrase" and "Image" buttons.
* Request a Phrase: Click the "Phrase" button to receive a random motivational phrase.
* Request an Image: Click the "Image" button. (Currently, this feature is a placeholder and not yet implemented.)

## Problems

### Issue with Telegram Bot when Chat History is Cleared

**Problem Description**

One significant challenge faced when developing Telegram bots is the inability to handle situations where users clear their chat history. 
This limitation arises due to the restrictions of the Telegram API, which does not provide methods for retrieving the complete message 
history of a chat or tracking the deletion of messages. As a result, when a user clears their chat history, the bot loses context and 
can become unresponsive, leading to a confusing user experience.

**Specifics of the Problem**

1. No Method to Retrieve All Messages:
    
The Telegram API does not offer a way to fetch the entire message history of a chat.
This limitation means that the bot cannot check previous interactions to maintain context or 
restore the state after the history has been cleared.

2. No Tracking of Message Deletions:

There are no API methods to track when messages are deleted by users.
This absence makes it impossible for the bot to be aware of when its context has been removed from the chat.

3. Inability to Verify if a Chat is Empty:

Since the bot cannot retrieve the chat history or track deletions, it cannot verify if a chat is entirely empty. 
This limitation is particularly problematic because it means the bot cannot determine whether 
it should send an introductory message or guide the user on how to start a new interaction.

4. Confusing User Experience:

Users who clear their chat history might not know that they need to send the /start command again to reinitialize the bot.
This situation can lead users to believe that the bot is not functioning correctly,
causing frustration and a negative user experience.

**Current Workarounds and Their Limitations**

1. Checking the Last Message:

The bot can check the last message in the chat to determine if it needs to reinitialize. 
However, this method is not foolproof and does not address the core issue of understanding the chat's overall state.

2. Regular Prompts:

The bot can periodically send prompts reminding users to use the /start command. 
While this might mitigate some confusion, it can be perceived as spammy and intrusive.
