import os
import time
from groq import Groq
from config.settings import settings

class GroqClient:
    def __init__(self, api_key: str = None, model: str = None):
        # Load env variables if not set
        if not api_key:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY", settings.GROQ_API_KEY)
            
        self.api_key = api_key
        self.model = model or settings.GROQ_MODEL
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError("GROQ_API_KEY is not set. Please add it to your .env file.")
            self._client = Groq(api_key=self.api_key)
        return self._client

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.0, max_retries: int = 3) -> str:
        """
        Calls Groq API with retries and exponential backoff.
        """
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Groq API error (Attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)
        return ""
