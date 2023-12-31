from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from category.routers import router as router_category
from user.routers import router as router_user
from post.routers import router as post_router
from webapp.routers.routers import router as web_router
from fastapi.staticfiles import StaticFiles
# pip install itsdangerous
from starlette.middleware.sessions import SessionMiddleware
from src.settings_env import SECRET_KEY_SESSION
from src.settings_env import REDIS_HOST
from redis import asyncio as aioredis

app = FastAPI(
    title="My_app_project"
)


# Кеширование
# pip install "fastapi-cache2[redis]"
@app.on_event("startup")
async def startup():
    """При старте проекта подключается к redis для кэширования"""
    redis = aioredis.from_url(f"redis://{REDIS_HOST}", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


# В сессии будем хранить сообщение для вывода при перенаправлении
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY_SESSION)

# Подключение статических файлов
# pip install aiofiles
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")

app.include_router(router_category)
app.include_router(router_user)
app.include_router(post_router)
app.include_router(web_router)
