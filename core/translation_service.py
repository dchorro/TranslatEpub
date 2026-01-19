import logging
from models.translation import TranslationMap, TranslationMapElement
from core.protocols import TranslatorClient, CacheRepository

logger = logging.getLogger(__name__)

class TranslationService:
    """
    Facade service that coordinates caching and API calls.
    The 'Brain' that decides how to fulfill a translation request.
    """
    def __init__(self, client: TranslatorClient, cache: CacheRepository):
        self.client = client
        self.cache = cache

    def translate(self, book_id: str, to_translate: TranslationMap, target_lang: str, use_cache: bool = True) -> TranslationMap:
        current_model = self.client.model
        needed_elements = []
        final_elements = []

        # 1. Logic: Decide what comes from cache
        if use_cache:
            for el in to_translate.elements:
                cached_text = self.cache.get_translation(book_id, current_model, el.id)
                if cached_text:
                    final_elements.append(TranslationMapElement(id=el.id, text=cached_text))
                else:
                    needed_elements.append(el)
        else:
            needed_elements = to_translate.elements

        # 2. Logic: Translate only what's missing
        if needed_elements:
            logger.info(f"Translating {len(needed_elements)} elements via API...")
            translated_batch = self.client.translate_batch(
                TranslationMap(elements=needed_elements), 
                target_lang
            )
            
            # Persist new translations
            self.cache.save_batch(book_id, current_model, translated_batch.elements)
            final_elements.extend(translated_batch.elements)

        # 3. Maintain original order (Optional but recommended for stability)
        # We re-sort based on the original request's ID list
        order_map = {el.id: i for i, el in enumerate(to_translate.elements)}
        final_elements.sort(key=lambda x: order_map.get(x.id, 999))

        return TranslationMap(elements=final_elements)