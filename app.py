from fastapi import FastAPI, Request as FastAPIRequest
from dotenv import load_dotenv
from openai import OpenAI
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
import psycopg2
import os
from messages_db import create_db_and_tables, insert_message, get_session_messages
from telegram import Bot, Update
from telegram.ext import Updater, MessageHandler, CallbackContext
from telegram.ext.filters import Filters

create_db_and_tables()


def get_db_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"], cursor_factory=RealDictCursor)


def insert_message(message_question, message_content, chat_id, role):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO messages (message_question, message_content, chat_id, role, created_date)
                    VALUES (%s, %s, %s, %s, NOW())
                """,
                    (message_question, message_content, chat_id, role),
                )
    except Exception as e:
        print(f"Error al insertar mensaje: {e}")


def get_session_messages(chat_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT message_question, message_content, chat_id, role FROM messages
                    WHERE chat_id = %s
                    ORDER BY created_date ASC
                    """,
                    (chat_id,),
                )
                messages = cur.fetchall()
                return messages
    except Exception as e:
        print(f"Error al recuperar mensajes: {e}")
        return []


load_dotenv()

GPT_TOKEN = OpenAI(api_key=os.getenv("GPT_TOKEN"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")




class Query(BaseModel):
    ask: str

def question(message_question, chat_id):
    if message_question:
        messages = get_session_messages(chat_id)

        context_messages = [
            {
                "role": "system",
                "content": "Eres un asistente muy amable y util, y espero que me ayudes a responder cada una de mis preguntas",
            }
        ]

        # Convert SQLModel objects to dict format for context
        for msg in messages:
            context_messages.append(
                {
                    "role": "user",
                    "content": msg.message_question,
                }
            )
            context_messages.append(
                {
                    "role": "assistant",
                    "content": msg.message_content,
                }
            )

        context_messages.append(
            {
                "role": "user",
                "content": message_question,
            }
        )

        completion = GPT_TOKEN.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=context_messages,
        )

        response_message = completion.choices[0].message

        insert_message(message_question, response_message.content, chat_id, "user")

        return {"message": response_message.content}
    
def handle_text(update: Update, context: CallbackContext):

    message = update.message.text
    chat_id = update.message.chat_id

    reply_text = "No se recibió ningún mensaje válido."

    if message:
        try:
            # Suponiendo que question devuelve un diccionario con una clave 'message'
            reply_dict = question(message, chat_id)
            reply_text = reply_dict['message']
        except Exception as e:
            reply_text = "Error llamando al servicio de ChatCompletion"

    # Envía reply_text como respuesta
    context.bot.send_message(chat_id=chat_id, text=reply_text)

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, handle_text))

    updater.start_polling()
    updater.idle()
if __name__ == '__main__':
    main()
