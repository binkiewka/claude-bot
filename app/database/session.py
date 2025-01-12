import os
from typing import AsyncGenerator
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from urllib.parse import quote_plus

class DatabaseManager:
    def __init__(self, database_url: str = None):
        """
        Initialize async database engine and session
        """
        if database_url is None:
            # Get credentials from environment
            user = os.getenv('POSTGRES_USER', 'claude')
            password = quote_plus(os.getenv('POSTGRES_DB_PASSWORD', ''))  # URL encode password
            host = os.getenv('POSTGRES_HOST', '127.0.0.1')
            port = os.getenv('POSTGRES_PORT', '5432')
            database = os.getenv('POSTGRES_DB', 'claude_bot')
            
            # Construct URL
            database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

        print(f"Connecting to database at: {host}:{port}/{database}")
        
        self.engine = create_async_engine(
            database_url,
            echo=True,
            poolclass=NullPool,
            connect_args={
                "server_settings": {
                    "application_name": "claude_bot"
                }
            }
        )
        
        self.async_session = sessionmaker(
            self.engine,
            expire_on_commit=False,
            class_=AsyncSession
        )

    async def init_models(self):
        """
        Create database tables
        """
        from .models import Base
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating database tables: {str(e)}")
            raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session
        """
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def check_connection(self) -> bool:
        """
        Test database connection
        """
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(sa.text("SELECT version();"))
                version = await result.scalar()
                print(f"Successfully connected to PostgreSQL. Version: {version}")
                return True
        except Exception as e:
            print(f"Database connection test failed: {str(e)}")
            return False

db_manager = DatabaseManager()
