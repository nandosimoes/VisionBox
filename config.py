import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-troque-em-producao")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "visionbox")
    # Vídeo usado quando um título ainda não tem video_url (demonstração)
    DEMO_VIDEO_URL = os.getenv(
        "DEMO_VIDEO_URL",
        "/static/videos/big-buck-bunny-trailer.mp4",
    )
