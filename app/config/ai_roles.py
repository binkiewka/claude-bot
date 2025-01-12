import os
from typing import Dict, Optional
import yaml

class AIRoleConfig:
    def __init__(self, config_path: str = 'config/ai_roles.yml'):
        self.config_path = config_path
        # Change to store roles per server
        self.server_roles: Dict[str, str] = {}
        self.roles: Dict[str, str] = {}
        self.load_roles()

    def load_roles(self):
        try:
            with open(self.config_path, 'r') as f:
                self.roles = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading AI roles: {e}")
            self.roles = {
                "default": "You are Claude, an AI assistant. Be helpful and concise.",
                "concise": "You aim to be direct and brief while maintaining helpfulness.",
                "creative": "You are focused on creative and imaginative responses.",
                "academic": "You provide detailed, academic-style responses with citations when possible."
            }
            self.save_roles()

    def save_roles(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self.roles, f)

    def get_role_prompt(self, server_id: str = None, role_name: str = "default") -> str:
        # If no server_id provided or no specific role set for server, use default
        if not server_id or server_id not in self.server_roles:
            return self.roles.get(role_name, self.roles["default"])
        
        # Get server-specific role
        current_role = self.server_roles.get(server_id)
        return self.roles.get(current_role, self.roles["default"])

    def set_server_role(self, server_id: str, role_name: str) -> bool:
        """Set role for specific server"""
        if role_name in self.roles:
            self.server_roles[server_id] = role_name
            return True
        return False

    def get_server_role(self, server_id: str) -> str:
        """Get current role for specific server"""
        return self.server_roles.get(server_id, "default")

    def add_role(self, name: str, prompt: str):
        self.roles[name] = prompt
        self.save_roles()

    def remove_role(self, name: str):
        if name != "default" and name in self.roles:
            del self.roles[name]
            self.save_roles()
