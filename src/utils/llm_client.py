"""HuggingFace Inference API client for LLM generation."""

import os
import time

import requests

PRIMARY_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
FALLBACK_MODEL = "HuggingFaceH4/zephyr-7b-beta"
API_BASE = "https://api-inference.huggingface.co/models"
TIMEOUT = 60


class HFInferenceClient:
    """Client for HuggingFace Inference API with retry and fallback logic."""

    def __init__(self):
        self.token = os.environ.get("HF_TOKEN", "")
        self.primary_model = PRIMARY_MODEL
        self.fallback_model = FALLBACK_MODEL
        self._active_model = self.primary_model

    @property
    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _call_api(self, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
        """Make a single API call to the HF Inference API."""
        url = f"{API_BASE}/{model}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        resp = requests.post(url, json=payload, headers=self._headers, timeout=TIMEOUT)
        resp.raise_for_status()

        data = resp.json()

        # Extract generated text from chat completion response
        choices = data.get("choices", [])
        if not choices:
            return ""

        message = choices[0].get("message", {})
        return message.get("content", "").strip()

    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1) -> str:
        """Generate text with retry and fallback logic.

        - 503 (model loading): exponential backoff, 3 attempts (5s/10s/20s)
        - 429 (rate limit): switch to fallback model
        - Empty/malformed: return empty string
        """
        backoff_delays = [5, 10, 20]
        model = self._active_model

        for attempt in range(3):
            try:
                result = self._call_api(model, prompt, max_tokens, temperature)
                return result

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else 0

                if status == 503:
                    # Model loading — backoff and retry
                    delay = backoff_delays[attempt] if attempt < len(backoff_delays) else 20
                    print(f"[LLM] Model loading (503), retrying in {delay}s (attempt {attempt + 1}/3)")
                    time.sleep(delay)
                    continue

                elif status == 429:
                    # Rate limited — switch to fallback
                    if model == self.primary_model and self.fallback_model:
                        print(f"[LLM] Rate limited (429), switching to fallback: {self.fallback_model}")
                        model = self.fallback_model
                        self._active_model = self.fallback_model
                        continue
                    else:
                        print("[LLM] Rate limited on fallback model, giving up")
                        return ""

                else:
                    print(f"[LLM] HTTP error {status}: {e}")
                    return ""

            except requests.exceptions.Timeout:
                print(f"[LLM] Timeout after {TIMEOUT}s (attempt {attempt + 1}/3)")
                continue

            except requests.exceptions.RequestException as e:
                print(f"[LLM] Request error: {e}")
                return ""

            except (KeyError, IndexError, TypeError) as e:
                print(f"[LLM] Malformed response: {e}")
                return ""

        print("[LLM] All retry attempts exhausted")
        return ""

    def classify(self, text: str, categories: list[str]) -> str:
        """Classify text into one of the given categories.

        Returns the best matching category string, or the first category
        if classification fails.
        """
        categories_str = ", ".join(categories)
        prompt = (
            f"Classify the following text into exactly one of these categories: {categories_str}\n\n"
            f"Text: {text}\n\n"
            f"Respond with ONLY the category name, nothing else."
        )

        result = self.generate(prompt, max_tokens=50, temperature=0.0)
        result = result.strip().strip("\"'`.").strip()

        # Check if the response matches one of the categories (case-insensitive)
        for cat in categories:
            if cat.lower() in result.lower() or result.lower() in cat.lower():
                return cat

        # Fallback: return first category
        return categories[0] if categories else ""
