"""
Configuration management for the backend.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Flask
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Server
    HOST = os.getenv('FLASK_HOST', 'localhost')
    PORT = int(os.getenv('FLASK_PORT', 5000))

    # SSL
    SSL_CERT_PATH = os.getenv('SSL_CERT_PATH', './backend/data/ssl/cert.pem')
    SSL_KEY_PATH = os.getenv('SSL_KEY_PATH', './backend/data/ssl/key.pem')

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://localhost:3000').split(',')

    # AI Provider
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'ollama')
    OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')

    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', './backend/data/database.db')
    VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', './backend/data/chroma_db')


config = Config()
