import pytest
from core.translation_service import TranslationService
from core.protocols import TranslatorClient, CacheRepository
from models.translation import TranslationMap, TranslationMapElement

# --- Mocks creados explícitamente gracias a los Protocolos ---

class MockTranslator:
    def __init__(self, model_name="mock-model"):
        self._model = model_name
        self.call_count = 0

    @property
    def model(self) -> str:
        return self._model

    def translate_batch(self, translation_map: TranslationMap, target_lang: str) -> TranslationMap:
        self.call_count += 1
        # Simplemente añadimos "[TRANS]" al texto para simular traducción
        translated_elements = [
            TranslationMapElement(id=el.id, text=f"[TRANS] {el.text}")
            for el in translation_map.elements
        ]
        return TranslationMap(elements=translated_elements)

class MockCache:
    def __init__(self):
        self.storage = {}
        self.save_count = 0

    def save_batch(self, book_id: str, model_name: str, elements: list[TranslationMapElement]) -> None:
        self.save_count += 1
        for el in elements:
            key = (book_id, model_name, el.id)
            self.storage[key] = el.text

    def get_translation(self, book_id: str, model_name: str, ref_id: str) -> str | None:
        return self.storage.get((book_id, model_name, ref_id))

# --- Tests ---

def test_translation_service_uses_cache():
    # Setup
    translator = MockTranslator()
    cache = MockCache()
    service = TranslationService(translator, cache)
    
    book_id = "test_book"
    elements = [TranslationMapElement(id="REF_001", text="Hello")]
    t_map = TranslationMap(elements=elements)
    
    # Pre-poblar caché
    cache.save_batch(book_id, translator.model, [TranslationMapElement(id="REF_001", text="Hola Cached")])
    
    # Execute
    result = service.translate(book_id, t_map, "spanish")
    
    # Verify
    assert result.elements[0].text == "Hola Cached"
    assert translator.call_count == 0  # No debería haber llamado a la API

def test_translation_service_calls_api_and_saves_cache():
    # Setup
    translator = MockTranslator()
    cache = MockCache()
    service = TranslationService(translator, cache)
    
    book_id = "test_book"
    elements = [TranslationMapElement(id="REF_002", text="World")]
    t_map = TranslationMap(elements=elements)
    
    # Execute
    result = service.translate(book_id, t_map, "spanish")
    
    # Verify
    assert result.elements[0].text == "[TRANS] World"
    assert translator.call_count == 1
    assert cache.get_translation(book_id, translator.model, "REF_002") == "[TRANS] World"
