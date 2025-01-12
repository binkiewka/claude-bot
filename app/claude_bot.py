import os
import asyncio
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, Optional, Set, List
from pathlib import Path

import discord
from discord.ext import commands, tasks

from app.services.claude_service import ClaudeService
from app.services.file_sharing_service import FileShareService
from app.services.logging_service import LoggingService
from app.services.rate_limiter import RateLimiter
from app.services.conversation_manager import ConversationManager
from app.services.queue_service import QueueService
from app.services.analytics_service import AnalyticsService
from app.utils.config import BotConfig
from app.utils.permissions import is_admin_or_bot_owner

class ClaudeBot(commands.Bot):
    def __init__(self):
        self.config = BotConfig.load()
        
        if not self.config.validate():
            raise ValueError("Invalid bot configuration")

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(
            command_prefix='!', 
            intents=intents,
            owner_ids=set(self.config.bot_owners)
        )

        self.logger = LoggingService()
        
        try:
            self.rate_limiter = RateLimiter(max_calls=self.config.max_messages_per_minute)
            self.claude_service = ClaudeService(api_key=self.config.claude_api_key)
            self.file_share_service = FileShareService(credentials_path='credentials/credentials.json')
            self.conversation_manager = ConversationManager()
            self.queue_service = QueueService()
            self.analytics_service = AnalyticsService(max_records=200)
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            self.logger.error(traceback.format_exc())
            raise

        # Initialize allowed channels as a dictionary of server_id to list of channel_ids
        self.allowed_channels: Dict[str, List[int]] = {}
        os.makedirs('logs', exist_ok=True)

    async def get_claude_response(self, user_id: str, message: str, channel_id: int, server_id: str) -> str:
        try:
            context = self.conversation_manager.get_context(channel_id)
            
            if context:
                message = f"Previous conversation:\n{context}\n\nNew message: {message}"
            
            response = await self.claude_service.get_response(
                user_id=user_id,
                message=message,
                channel_id=channel_id,
                server_id=server_id
            )
            
            self.conversation_manager.add_message(channel_id, message, is_bot=False)
            self.conversation_manager.add_message(channel_id, response, is_bot=True)
            
            return response
        except Exception as e:
            self.logger.error(f"Error in get_claude_response: {str(e)}")
            self.analytics_service.add_error("claude_response", str(e))
            return "I encountered an error processing your request. Please try again."

    async def clear_conversation_context(self, channel_id: int):
        self.conversation_manager.clear_context(channel_id)

    async def setup_hook(self):
        try:
            await self.load_allowed_channels()

            extensions = [
                'app.cogs.claude_cog',
                'app.cogs.admin_cog'
            ]

            for ext in extensions:
                try:
                    await self.load_extension(ext)
                    self.logger.info(f"Loaded extension: {ext}")
                except Exception as ext_error:
                    self.logger.error(f"Failed to load extension {ext}: {ext_error}")
                    self.logger.error(traceback.format_exc())

            self.logger.info("Bot setup completed successfully")
        except Exception as e:
            self.logger.error(f"Failed during setup: {e}")
            self.logger.error(traceback.format_exc())

    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user}")
        self.logger.info(f"Connected to {len(self.guilds)} guilds")

    async def on_guild_join(self, guild):
        if not self.config.allowed_guilds:
            self.logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
            return

        if guild.id in self.config.allowed_guilds:
            self.logger.info(f"Joined allowed guild: {guild.name} (ID: {guild.id})")
        else:
            await guild.leave()
            self.logger.warning(f"Left unauthorized guild: {guild.name} (ID: {guild.id})")

    async def on_error(self, event_method: str, *args, **kwargs):
        self.logger.error(f'Error in {event_method}')
        self.logger.error(traceback.format_exc())
        self.analytics_service.add_error("event", traceback.format_exc())

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.errors.CommandNotFound):
            return
        else:
            self.logger.error(f"Command error: {error}")
            self.logger.error(traceback.format_exc())
            self.analytics_service.add_error("command", str(error))
            await ctx.send(f"An error occurred: {str(error)}")

    async def save_allowed_channels(self):
        try:
            allowed_channels_path = Path('logs/allowed_channels.json')
            allowed_channels_path.parent.mkdir(parents=True, exist_ok=True)
            
            with allowed_channels_path.open('w') as f:
                json.dump(self.allowed_channels, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save allowed channels: {e}")
            self.logger.error(traceback.format_exc())

    async def load_allowed_channels(self):
        try:
            allowed_channels_path = Path('logs/allowed_channels.json')
            if allowed_channels_path.exists():
                with allowed_channels_path.open('r') as f:
                    data = json.load(f)
                    
                    # Initialize empty channel dict
                    self.allowed_channels = {}
                    
                    # Handle both old and new format
                    for server_id, channels in data.items():
                        if isinstance(channels, list):
                            # New format - already a list
                            self.allowed_channels[server_id] = [int(cid) for cid in channels]
                        else:
                            # Old format - single channel ID
                            self.allowed_channels[server_id] = [int(channels)]
                            
                    # Save in new format
                    await self.save_allowed_channels()
            else:
                self.allowed_channels = {}
        except Exception as e:
            self.logger.error(f"Failed to load allowed channels: {e}")
            self.logger.error(traceback.format_exc())
            self.allowed_channels = {}

async def main():
    bot = ClaudeBot()
    try:
        await bot.start(bot.config.discord_token)
    except Exception as e:
        print(f"Bot startup failed: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
