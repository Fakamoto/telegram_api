from sqlmodel import SQLModel, Session, create_engine
from dotenv import load_dotenv
import os
from models import Message

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    """Create database tables"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session

def insert_message(message_question: str, message_content: str, chat_id: int, role: str):
    """Insert a new message into the database"""
    try:
        with Session(engine) as session:
            message = Message(
                message_question=message_question,
                message_content=message_content,
                chat_id=chat_id,
                role=role
            )
            session.add(message)
            session.commit()
    except Exception as e:
        print(f"Error inserting message: {e}")

def get_session_messages(chat_id: int):
    """Get all messages for a specific chat_id"""
    try:
        with Session(engine) as session:
            messages = session.query(Message).filter(
                Message.chat_id == chat_id
            ).order_by(Message.created_date.asc()).all()
            return messages
    except Exception as e:
        print(f"Error retrieving messages: {e}")
        return []
