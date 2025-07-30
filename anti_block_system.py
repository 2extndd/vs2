import random
import time
import requests
from datetime import datetime

# Anti-blocking system
class VintedAntiBlock:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
        ]
        self.request_count = 0
        self.last_request_time = 0
        
    def get_random_headers(self):
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
    
    def smart_delay(self):
        """Intelligent delay between requests"""
        self.request_count += 1
        current_time = time.time()
        
        # Base delay: 3-7 seconds
        base_delay = random.uniform(3, 7)
        
        # Progressive delay after many requests
        if self.request_count % 10 == 0:
            base_delay += random.uniform(10, 20)  # Extra delay every 10 requests
            
        if self.request_count % 50 == 0:
            base_delay += random.uniform(60, 120)  # Long break every 50 requests
            
        # Avoid too frequent requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < 2:
            base_delay += random.uniform(2, 5)
            
        logging.info(f"🕐 Smart delay: {base_delay:.1f}s (request #{self.request_count})")
        time.sleep(base_delay)
        self.last_request_time = time.time()
        
    def handle_rate_limit(self, response):
        """Handle rate limiting responses"""
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After', 300)
            wait_time = int(retry_after) + random.uniform(60, 180)
            logging.warning(f"🚫 Rate limited! Waiting {wait_time:.0f}s")
            add_error(f"Rate limit: waiting {wait_time:.0f}s")
            time.sleep(wait_time)
            return True
        elif response.status_code in [403, 406, 503]:
            wait_time = random.uniform(300, 600)  # 5-10 minutes
            logging.warning(f"🔒 Blocked (HTTP {response.status_code})! Waiting {wait_time:.0f}s")
            add_error(f"Blocked {response.status_code}: waiting {wait_time:.0f}s")
            time.sleep(wait_time)
            return True
        return False

# Global anti-block instance
anti_block = VintedAntiBlock()
