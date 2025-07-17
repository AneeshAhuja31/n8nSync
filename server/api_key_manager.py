import os
import random
from dotenv import load_dotenv
load_dotenv()

class APIKeyManager:
    def __init__(self):
        self.keys = []
        i = 1
        while True:
            key = os.getenv(f"GEMINI_API_KEY_{i}")
            if key:
                self.keys.append(key)
                i += 1
            else:
                break
                
        self.last_key_index = -1
        
    def get_next_key(self) -> str:
        self.last_key_index = (self.last_key_index + 1) % len(self.keys)
        return self.keys[self.last_key_index]
        
    def get_random_key(self) -> str:
        return random.choice(self.keys)