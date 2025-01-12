from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import statistics

class AnalyticsService:
    def __init__(self, max_records: int = 200):
        self.max_records = max_records
        self.mentions: List[Dict] = []
        self.response_times: Dict[int, List[float]] = defaultdict(list)
        self.channel_usage: Dict[int, int] = defaultdict(int)
        self.errors: List[Dict] = []
        self.start_time = datetime.now()

    def add_mention(self, channel_id: int, user_id: str, content: str):
        self.mentions.append({
            'timestamp': datetime.now(),
            'channel_id': channel_id,
            'user_id': user_id,
            'content': content
        })
        self.channel_usage[channel_id] += 1
        self._trim_records()

    def add_response_time(self, channel_id: int, response_time: float):
        self.response_times[channel_id].append(response_time)

    def add_error(self, error_type: str, error_message: str):
        self.errors.append({
            'timestamp': datetime.now(),
            'type': error_type,
            'message': error_message
        })

    def get_stats(self) -> Dict:
        now = datetime.now()
        uptime = now - self.start_time
        
        total_mentions = len(self.mentions)
        total_errors = len(self.errors)
        error_rate = (total_errors / total_mentions) if total_mentions > 0 else 0

        avg_response_times = {
            channel_id: statistics.mean(times) if times else 0
            for channel_id, times in self.response_times.items()
        }

        most_active_channels = sorted(
            self.channel_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            'uptime': str(uptime).split('.')[0],
            'total_mentions': total_mentions,
            'error_rate': f"{error_rate:.2%}",
            'avg_response_times': avg_response_times,
            'most_active_channels': most_active_channels,
            'queued_messages': sum(len(self.mentions) for _ in self.mentions),
        }

    def _trim_records(self):
        if len(self.mentions) > self.max_records:
            self.mentions = self.mentions[-self.max_records:]
