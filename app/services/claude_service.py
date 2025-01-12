import json
import asyncio
import aiohttp
from typing import List, Dict, Optional
from app.config.ai_roles import AIRoleConfig
import os

class ClaudeService:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Claude service with API key"""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("No API key provided for Claude service")
        
        self.model = "claude-3-5-haiku-20241022"
        self.max_tokens = 1000
        self.headers = {
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "x-api-key": self.api_key
        }
        self.role_config = AIRoleConfig()

    async def get_response(
        self,
        user_id: str,
        message: str,
        channel_id: int,
        server_id: str = None,
        max_tokens: int = 1000
    ) -> str:
        """Get a response from Claude"""
        try:
            system_prompt = self.role_config.get_role_prompt(server_id)
            
            data = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "messages": [{
                    "role": "user",
                    "content": message
                }],
                "system": system_prompt
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=self.headers,
                    json=data,
                    timeout=30
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API Error {response.status}: {error_text}")
                    
                    response_data = await response.json()
                    if 'content' not in response_data or not response_data['content']:
                        raise Exception("Empty response from API")
                    
                    return response_data['content'][0]['text']

        except Exception as e:
            print(f"Error in Claude service: {str(e)}")
            return f"I encountered an error: {str(e)}"

    async def get_stream_response(
        self,
        user_id: str,
        message: str,
        channel_id: int,
        server_id: str = None,
        max_tokens: int = 1000
    ) -> asyncio.StreamReader:
        """Get a streaming response from Claude"""
        try:
            system_prompt = self.role_config.get_role_prompt(server_id)
            
            data = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "messages": [{
                    "role": "user",
                    "content": message
                }],
                "system": system_prompt,
                "stream": True
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=self.headers,
                    json=data,
                    timeout=30
                ) as response:
                    if response.status != 200:
                        raise Exception(f"API Error: {response.status}")
                    return response.content

        except Exception as e:
            print(f"Error in Claude streaming service: {str(e)}")
            raise

    def validate_response(self, response: str) -> bool:
        """Validate Claude's response"""
        if not response or len(response.strip()) == 0:
            return False
        return True
