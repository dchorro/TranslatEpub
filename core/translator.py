import requests
from models.translation import TranslationMapElement, TranslationMap
from models.usage import UsageStatistics
from prompts import PROMPTS_DICT
from core.config import settings
from core.protocols import TranslationValidator
from core.validators import TranslationValidationError, IDAlignmentValidator
import time
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    before_sleep_log
)

logger = logging.getLogger(__name__)


def is_api_transient_error(exception):
    """Checks if the exception is a 429, 5xx, or a validation error that warrants a retry."""
    if isinstance(exception, TranslationValidationError):
        return True
    if isinstance(exception, requests.exceptions.HTTPError) and exception.response is not None:
        return exception.response.status_code == 429 or 500 <= exception.response.status_code < 600
    return False


class OpenRouterClient:
    """Handles communication with OpenRouter API."""
    # "google/gemini-2.0-flash-exp:free"
    # "xiaomi/mimo-v2-flash:free"

    # "mistralai/devstral-2512:free"
    # "meta-llama/llama-3.3-70b-instruct:free"
    def __init__(self, api_key: str, stats: UsageStatistics, model: str = settings.default_model, validator: TranslationValidator = None):
        self.api_key = api_key
        self.model = model
        self.stats = stats
        self.url = f"{settings.openrouter_base_url}/chat/completions"
        self.price_per_token_prompt = 0.0
        self.price_per_token_completion = 0.0
        # Por defecto usamos el validador de IDs si no se provee ninguno
        self.validator = validator or IDAlignmentValidator()

    def fetch_model_prices(self):
        """Fetches the current pricing for the configured model from OpenRouter."""
        response = requests.get(f"{settings.openrouter_base_url}/models")
        if response.status_code == 200:
            models = response.json().get("data", [])
            # Buscamos nuestro modelo en la listal
            model_info = next((m for m in models if m["id"] == self.model), None)
            if model_info:
                # OpenRouter devuelve precios por 1M de tokens
                pricing = model_info.get("pricing", {})
                self.price_per_token_prompt = float(pricing.get("prompt", 0))
                self.price_per_token_completion = float(pricing.get("completion", 0))
                logger.info(f"Pricing loaded for {self.model}: ${self.price_per_token_prompt}/1M prompt | ${self.price_per_token_completion}/1M prompt")

    def translate_batch(self, translation_map: TranslationMap, target_lang: str, batch_size: int = 80) -> TranslationMap:
        """Translates the map in smaller chunks to avoid Rate Limits (Error 429)."""
        all_translated_elements = []
        elements = translation_map.elements
        system_prompt = PROMPTS_DICT.get(target_lang)

        # Split elements into smaller lists
        for i in range(0, len(elements), batch_size):
            batch = elements[i : i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} elements)...")
            logger.info(f"Sending {batch=}")
            
            translated_elements = self._send_request(batch, system_prompt)
            all_translated_elements.extend(translated_elements)
            
            # Wait 2-3 seconds between batches to avoid the 429 error
            if i + batch_size < len(elements):
                logger.info("Waiting to avoid Rate Limit...")
                time.sleep(3)

        return TranslationMap(elements=all_translated_elements)

    @retry(
        retry=retry_if_exception(is_api_transient_error),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _send_request(self, batch: list[TranslationMapElement], system_prompt: str) -> list[TranslationMapElement]:
        """Internal method to handle a single API call."""
        prompt_content = "\n".join([f"{el.id}: {el.text}" for el in batch])
        json_schema = TranslationMap.model_json_schema()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_content}
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "translation_map",
                    "strict": True,
                    "schema": json_schema
                }
            }
        }

        response = requests.post(self.url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        self.stats.add_usage(
            prompt=prompt_tokens,
            completion=completion_tokens,
            price_prompt_1m=self.price_per_token_prompt,
            price_completion_1m=self.price_per_token_completion
        )
        
        logger.info(f"Batch Usage: {prompt_tokens} prompt, {completion_tokens} completion tokens.")

        raw_json = response.json()["choices"][0]["message"]["content"]
        try:
            translated_map = TranslationMap.model_validate_json(raw_json)
            
            # Ejecutamos la lógica de validación desacoplada
            self.validator.validate(batch, translated_map)
            
            return translated_map.elements
            
        except (TranslationValidationError, Exception) as e:
            if isinstance(e, TranslationValidationError):
                raise e
            logger.error(f"Validation failed. Response content: {raw_json}")
            raise e