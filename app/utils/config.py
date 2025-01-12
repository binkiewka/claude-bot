import os
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class BotConfig:
    """
    Comprehensive configuration management
    Supports multiple configuration sources
    """
    discord_token: str = field(default_factory=lambda: os.getenv('DISCORD_TOKEN', ''))
    claude_api_key: str = field(default_factory=lambda: os.getenv('CLAUDE_API_KEY', ''))
    
    # Advanced configuration options
    allowed_guilds: List[int] = field(default_factory=list)
    bot_owners: List[int] = field(default_factory=list)
    
    # Logging and monitoring
    log_level: str = 'INFO'
    error_webhook_url: Optional[str] = None
    
    # Rate limiting
    max_messages_per_minute: int = 10
    
    @classmethod
    def load(cls):
        """
        Load configuration from multiple sources
        Prioritizes environment variables, then falls back to defaults
        """
        return cls(
            discord_token=os.getenv('DISCORD_TOKEN', ''),
            claude_api_key=os.getenv('CLAUDE_API_KEY', ''),
            allowed_guilds=[
                int(guild_id) for guild_id in 
                os.getenv('ALLOWED_GUILDS', '').split(',') 
                if guild_id
            ],
            bot_owners=[
                int(owner_id) for owner_id in 
                os.getenv('BOT_OWNERS', '').split(',') 
                if owner_id
            ],
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            error_webhook_url=os.getenv('ERROR_WEBHOOK_URL'),
            max_messages_per_minute=int(
                os.getenv('MAX_MESSAGES_PER_MINUTE', '10')
            )
        )

    def validate(self) -> bool:
        """
        Validate configuration
        
        :return: Boolean indicating if configuration is valid
        """
        errors = []
        
        if not self.discord_token:
            errors.append("Discord token is required")
        
        if not self.claude_api_key:
            errors.append("Claude API key is required")
        
        if errors:
            print("Configuration Errors:")
            for error in errors:
                print(f"- {error}")
            return False
        
        return True

    def get_safe_config(self) -> dict:
        """
        Return a safe version of the configuration (without sensitive data)
        
        :return: Dictionary of safe configuration values
        """
        return {
            'allowed_guilds': self.allowed_guilds,
            'bot_owners': self.bot_owners,
            'log_level': self.log_level,
            'max_messages_per_minute': self.max_messages_per_minute
        }
