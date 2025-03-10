import os
import logging
from random import choice
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InputFile
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import NetworkError, TelegramError
from utils import load_phrases_from_file, get_random_phrase


class NIASupportBot:
    def __init__(self, application, phrases_filename: str, img_dirs: list):
        """
        Initialize the bot with the given application and load phrases from file.

        Args:
            application: The Telegram application instance.
        """
        self.application = application
        self.phrases = load_phrases_from_file(phrases_filename)
        self.img_dirs = img_dirs
        self.is_started = False  # Track if the bot is started

    def get_username(self, user) -> str:
        """
        Generate a string with user details.

        Args:
            user: The user object.

        Returns:
            str: A string with user details in the format:
                 <ID> (<nickname>) [Full Name] (birth date | status)
        """
        user_id = user.id
        username = user.username or ""
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        bio = user.bio if hasattr(user, "bio") else None
        birth_date = user.birth_date if hasattr(user, "birth_date") else None

        result = f"{user_id} ({username}) [{full_name}]"
        if birth_date:
            result += f" ({birth_date})"
        elif bio:
            result += f" ({bio})"

        return result

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle the /start command. This function sends a message with a custom keyboard.

        Args:
            update (Update): Incoming update.
            context (ContextTypes.DEFAULT_TYPE): Callback context.
        """
        user = update.effective_user
        username = self.get_username(user)
        self.is_started = True

        try:
            # Create a custom keyboard with "Фраза" and "Картинка" buttons
            custom_keyboard = [[KeyboardButton("Фраза"), KeyboardButton("Картинка")]]
            reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)

            # Send message with the custom keyboard
            await update.message.reply_text(
                "Бот запущен. Выберите опцию:", reply_markup=reply_markup
            )
            logging.info(f"User {username} started the bot.")
        except TelegramError as e:
            logging.error(f"Telegram error for user {username}: {e}")
            await update.message.reply_text(
                "An error occurred while processing your request. Please try again later."
            )

    async def send_phrase(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle the "Фраза" button click event. This function sends a random phrase.

        Args:
            update (Update): Incoming update.
            context (ContextTypes.DEFAULT_TYPE): Callback context.
        """
        user = update.effective_user
        username = self.get_username(user)

        try:
            random_phrase = get_random_phrase(self.phrases)
            await update.message.reply_text(random_phrase)
            logging.info(
                f"User {username} requested the phrase. Response is: {random_phrase}"
            )
        except NetworkError as e:
            logging.error(f"Network error: {e}")
            await update.message.reply_text(
                "A network error occurred. Please try again later."
            )
        except TelegramError as e:
            logging.error(f"Telegram error: {e}")
            await update.message.reply_text(
                "An error occurred while processing your request. Please try again later."
            )

    async def send_image(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle the "Картинка" button click event.

        Args:
            update (Update): Incoming update.
            context (ContextTypes.DEFAULT_TYPE): Callback context.
        """
        user = update.effective_user
        username = self.get_username(user)

        try:
            # Collect all image files from the provided directories
            img_files = []
            for directory in self.img_dirs:
                img_files.extend(
                    [
                        os.path.join(directory, f)
                        for f in os.listdir(directory)
                        if os.path.isfile(os.path.join(directory, f))
                    ]
                )

            if not img_files:
                await update.message.reply_text("No images found in the directories.")
                return

            # Select a random file
            random_img = choice(img_files)

            # Log the image path
            logging.info(f"Sending image: {random_img}")

            # Read the image as bytes
            with open(random_img, "rb") as img_file:
                await update.message.reply_photo(photo=img_file)

            logging.info(
                f"User {username} requested an image. Sent image: {random_img}"
            )

        except TelegramError as e:
            logging.error(f"Telegram error: {e}")
            await update.message.reply_text(
                "An error occurred while processing your request. Please try again later."
            )

    async def log_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Log incoming messages and delegate to appropriate handlers.

        Args:
            update (Update): Incoming update.
            context (ContextTypes.DEFAULT_TYPE): Callback context.
        """
        user = update.effective_user
        username = self.get_username(user)
        message = update.message.text

        logging.info(f"Received message from user {username}: {message}")

        # Delegate to specific handlers
        if message == "Фраза":
            await self.send_phrase(update, context)
        elif message == "Картинка":
            await self.send_image(update, context)

    def register_handlers(self):
        """
        Register command and callback handlers.
        """
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.log_message)
        )
