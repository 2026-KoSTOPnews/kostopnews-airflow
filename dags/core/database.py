from core.config import settings

# -------------------------
# DB 설정
# -------------------------
DB_CONFIG = {
    "host": settings.POSTGRES_HOST,
    "database": settings.POSTGRES_DB,
    "user": settings.POSTGRES_USER,
    "password": settings.POSTGRES_PASSWORD,
    "port": settings.POSTGRES_PORT,
}