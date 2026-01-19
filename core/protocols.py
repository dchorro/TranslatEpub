from typing import Protocol, runtime_checkable
from models.translation import TranslationMap, TranslationMapElement

@runtime_checkable
class TranslatorClient(Protocol):
    """Interfaz para clientes de traducción (OpenRouter, DeepSeek, etc)."""
    @property
    def model(self) -> str: ...
    
    def translate_batch(self, translation_map: TranslationMap, target_lang: str) -> TranslationMap:
        """Debe traducir un batch de elementos."""
        ...

@runtime_checkable
class CacheRepository(Protocol):
    """Interfaz para sistemas de persistencia/caché."""
    def save_batch(self, book_id: str, model_name: str, elements: list[TranslationMapElement]) -> None:
        """Guarda un conjunto de traducciones."""
        ...

    def get_translation(self, book_id: str, model_name: str, ref_id: str) -> str | None:
        """Recupera una traducción específica."""
        ...

@runtime_checkable
class TranslationValidator(Protocol):
    """Interfaz para validadores de respuesta del LLM."""
    def validate(self, original_elements: list[TranslationMapElement], translated_map: TranslationMap) -> None:
        """Debe lanzar TranslationValidationError si falla."""
        ...
