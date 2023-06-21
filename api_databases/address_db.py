from src.settings_env import (
    POSTGRES_USER as postg_user,
    POSTGRES_PASSWORD as postg_password,
    POSTGRES_HOST as postg_host,
    POSTGRES_PORT as postg_port,
    POSTGRES_DB as postg_db
)

_URL_DATABASE = f'postgresql+asyncpg://{postg_user}:{postg_password}@{postg_host}:{postg_port}/{postg_db}'
