import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    # BOOTSTRAP_SETUP_KEY = os.getenv("BOOTSTRAP_SETUP_KEY")    

    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("Falta configurar DATABASE_URL en .env")

    if not JWT_SECRET_KEY:
        raise RuntimeError("Falta configurar JWT_SECRET_KEY en .env")