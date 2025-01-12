import os
from typing import Dict, Optional
import yaml

class AIRoleConfig:
    def __init__(self, config_path: str = 'config/ai_roles.yml'):
        self.config_path = config_path
        self.current_role: Optional[str] = None
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

    def get_role_prompt(self, role_name: str = "default") -> str:
        return self.roles.get(role_name, self.roles["default"])

    def add_role(self, name: str, prompt: str):
        self.roles[name] = prompt
        self.save_roles()

    def remove_role(self, name: str):
        if name != "default" and name in self.roles:
            del self.roles[name]
            self.save_roles()
