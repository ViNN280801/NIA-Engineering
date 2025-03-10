import logging
from os import makedirs
from os.path import exists, join
from datetime import datetime
from telegram.ext import Application
from bot import NIASupportBot, NIA_SUPPORT_BOT_TOKEN


log_directory = "logs"
if not exists(log_directory):
    makedirs(log_directory)
log_filename = join(
    log_directory, f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_filename, encoding="utf-8"),
    ],
    encoding="utf-8",
)


def main() -> None:
    """
    Start the bot and register command and callback handlers.
    """
    try:
        application = Application.builder().token(NIA_SUPPORT_BOT_TOKEN).build()

        img_dirs = ["resources/imgs/motivation/"]
        my_bot = NIASupportBot(application, "resources/phrases.txt", img_dirs)
        my_bot.register_handlers()
        application.run_polling()

    except Exception as e:
        logging.error(f"Failed to start the bot: {e}")


if __name__ == "__main__":
    main()
