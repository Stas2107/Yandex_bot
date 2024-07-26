import aiohttp
import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command
from config import TOKEN, YANDEX_CAT, YANDEX_GPT
import copy

# Настройки логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки YandexGPT API
url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Api-Key {YANDEX_GPT}"
}

# Инициализация бота и диспетчера
API_TOKEN = TOKEN
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

prompt_template = {
    "modelUri": f"gpt://{YANDEX_CAT}/yandexgpt-lite",
    "completionOptions": {
        "stream": False,
        "temperature": 0.6,
        "maxTokens": 2000
    },
    "messages": []
}

# Функция для запроса к YandexGPT API
async def get_gpt_response(user_message: str):
    prompt = copy.deepcopy(prompt_template)
    prompt["messages"] = [
        {"role": "system", "text": "Ты ассистент дроид, отвечай как робот"},
        {"role": "user", "text": user_message}
    ]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=prompt) as response:
                response.raise_for_status()
                result = await response.json()

                # Логируем полный ответ от API
                logger.info(f"API response: {result}")

                if 'result' in result and 'alternatives' in result['result']:
                    alternatives = result['result']['alternatives']
                    if alternatives:
                        return alternatives[0]['message']['text']
                logger.warning("No valid choices in the API response.")
                return "Извините, я не могу сейчас ответить."
    except aiohttp.ClientResponseError as errh:
        logger.error(f"HTTP Error: {errh}")
        return f"HTTP Error: {errh}"
    except aiohttp.ClientConnectionError as errc:
        logger.error(f"Connection Error: {errc}")
        return f"Connection Error: {errc}"
    except aiohttp.ClientTimeout as errt:
        logger.error(f"Timeout Error: {errt}")
        return f"Timeout Error: {errt}"
    except aiohttp.ClientError as err:
        logger.error(f"Something went wrong: {err}")
        return f"Something went wrong: {err}"

    # Обработчик команды /start
@router.message(Command(commands=['start', 'help']))
async def send_welcome(message: Message):
    await message.answer("Привет! Я ассистент дроид.")

    # Обработчик обычных сообщений
@router.message()
async def handle_message(message: Message):
    user_message = message.text
    logger.info(f"Received message: {user_message}")
    response_text = await get_gpt_response(user_message)
    await message.answer(response_text)

    # Основная функция для запуска бота
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")