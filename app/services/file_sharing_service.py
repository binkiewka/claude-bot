import os
import io
import re
import json
from typing import Optional
from datetime import datetime

import aiohttp
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

class FileShareService:
    SCOPES = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.metadata.readonly'
    ]

    def __init__(self, drive_credentials_path: Optional[str] = None, credentials_path: Optional[str] = None):
        self.drive_service = None
        self.credentials_path = credentials_path or drive_credentials_path or 'credentials/credentials.json'
        
        if os.path.exists(self.credentials_path):
            try:
                self._setup_drive_credentials()
            except Exception as e:
                print(f"Failed to setup Drive credentials: {e}")

    def _setup_drive_credentials(self):
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=self.SCOPES
            )
            self.drive_service = build('drive', 'v3', credentials=credentials)
            print("Google Drive service account credentials loaded successfully.")
        
        except Exception as e:
            print(f"Service account credential setup failed: {e}")
            import traceback
            traceback.print_exc()

    def _format_for_paste(self, content: str) -> str:
        formatted_content = content
        formatted_content = re.sub(r'^(\d+)\.\s*', r'\1. ', formatted_content, flags=re.MULTILINE)
        formatted_content = re.sub(r'(\d+\. .+)\n(?!\d+\.|\n)', r'\1\n\n', formatted_content)
        formatted_content = re.sub(r'(?<=[.!?])\s+(?=[A-Z])', '\n', formatted_content)
        formatted_content = re.sub(r'\n{3,}', '\n\n', formatted_content)
        formatted_content = re.sub(r'```(\w+)\n', r'```\1\n', formatted_content)
        formatted_content = re.sub(r'\n```\n', r'\n\n```\n', formatted_content)
        return formatted_content.strip()

    def _contains_code(self, text: str) -> bool:
        return bool(
            re.search(r'```[\w\s]*\n.*?```', text, re.DOTALL) or
            re.search(r'\b(apt|sudo|docker|git|npm|pip)\b', text) or
            re.search(r'(/[\w/.-]+)|(\w+\.\w+)', text)
        )

    async def _upload_to_rentry(self, content: str) -> Optional[str]:
        try:
            formatted_content = self._format_for_paste(content)
            session = requests.Session()
            response = session.get('https://rentry.org')
            csrf_token = re.search(r'name="csrfmiddlewaretoken" value="(.+?)"', response.text)
            
            if not csrf_token:
                raise ValueError("Could not get CSRF token from Rentry.co")
                
            csrf_token = csrf_token.group(1)
            
            url = 'https://rentry.org/api/new'
            headers = {
                'Origin': 'https://rentry.org',
                'Referer': 'https://rentry.org',
                'Cookie': f'csrftoken={csrf_token}'
            }
            
            data = {
                'csrfmiddlewaretoken': csrf_token,
                'text': formatted_content,
                'edit_code': ''
            }
            
            response = session.post(url, data=data, headers=headers, timeout=10)
            
            if response.status_code != 200:
                raise ValueError(f"Rentry.co API error: Status {response.status_code}")
                
            result = response.json()
            if 'url' not in result:
                raise ValueError(f"Invalid response from Rentry.co: {result}")
                
            return result['url']
            
        except requests.exceptions.RequestException as e:
            print(f"Rentry request error: {str(e)}")
        except ValueError as e:
            print(f"Rentry value error: {str(e)}")
        except Exception as e:
            print(f"Unexpected Rentry error: {str(e)}")
        
        return None

    async def _upload_to_drive(self, content: str) -> Optional[str]:
        if not self.drive_service:
            return None

        try:
            formatted_content = self._format_for_paste(content)
            file_metadata = {
                'name': f'claude_response_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt',
                'mimeType': 'text/plain'
            }
            
            file_content = io.BytesIO(formatted_content.encode('utf-8'))
            media = MediaIoBaseUpload(file_content, mimetype='text/plain', resumable=True)
            file = self.drive_service.files().create(
                body=file_metadata, 
                media_body=media, 
                fields='id, webViewLink'
            ).execute()
            
            self.drive_service.permissions().create(
                fileId=file['id'],
                body={
                    'type': 'anyone',
                    'role': 'reader'
                }
            ).execute()
            
            return file.get('webViewLink', '')
        
        except Exception as e:
            print(f"Drive upload error: {e}")
            return None

    async def share_long_content(self, content: str) -> str:
        if len(content) <= 350:
            return content

        rentry_link = await self._upload_to_rentry(content)
        if rentry_link:
            return f"Full response available at: <{rentry_link}>"

        drive_link = await self._upload_to_drive(content)
        if drive_link:
            return f"Full response available at: <{drive_link}>"

        return f"{content[:350]}..."
