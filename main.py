import os
import telebot
import speech_recognition as sr
from gtts import gTTS
from g4f.client import Client

# Токен вашего бота
TOKEN = 'Your_BOT_TOKEN'
bot = telebot.TeleBot(TOKEN)

client = Client()

@bot.message_handler(commands=['speech-to-text'])
def handle_speech_to_text(message):
    bot.reply_to(message, "Пожалуйста, отправьте аудиофайл для распознавания речи.")

@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    try:
        # Получение информации о файле
        file_info = bot.get_file(message.audio.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Сохранение аудиофайла
        file_name = 'audio.ogg'  # Имя временного файла
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # Получение текста из аудиофайла
        text = audio_to_text(file_name)
        
        # Удаление временного аудиофайла
        os.remove(file_name)
        
        if text:
            # Отправка запроса на редактирование текста к ChatGPT
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": f"Hi! You're in the role of proofreader. See your task is that you proanilize the text that I will give you at the end of the corrected errors in it to tighten the grammar without changing the context of the text itself. Write only the text without additional messages like “Hi, here's your corrected text”. Here's the text itself: {text}"
                }]
            )

            # Отправка исправленного текста пользователю
            bot.reply_to(message, response.choices[0].message.content)
        else:
            bot.reply_to(message, "Не удалось распознать речь в аудиофайле")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

def audio_to_text(name_file):
    # Инициализация распознавателя
    recognizer = sr.Recognizer()
    
    # Загрузка аудиофайла
    with sr.AudioFile(name_file) as source:
        audio_data = recognizer.record(source)
    
    # Попытка распознавания речи в аудиофайле
    try:
        text = recognizer.recognize_google(audio_data, language="ru-RU")
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        return None

@bot.message_handler(commands=['text-to-speech'])
def handle_text_to_speech(message):
    bot.reply_to(message, "Введите текст, который вы хотите преобразовать в аудиофайл.")
    bot.register_next_step_handler(message, choose_language)

def choose_language(message):
    try:
        text = message.text
        bot.reply_to(message, "Выберите язык для аудиофайла (например, ru, en, fr):")
        bot.register_next_step_handler(message, convert_text_to_speech, text)
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

def convert_text_to_speech(message, text):
    try:
        language = message.text
        tts = gTTS(text, lang=language)
        tts.save('output.mp3')
        with open('output.mp3', 'rb') as audio:
            bot.send_audio(message.chat.id, audio)
        os.remove('output.mp3')
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

bot.polling()
