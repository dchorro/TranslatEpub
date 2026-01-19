from core.protocols import TranslationValidator
from models.translation import TranslationMap, TranslationMapElement

class TranslationValidationError(Exception):
    """Excepción base para errores de validación de traducción."""
    pass

class IDAlignmentValidator:
    """Valida que los IDs recibidos coincidan exactamente con los enviados."""
    def validate(self, original_elements: list[TranslationMapElement], translated_map: TranslationMap) -> None:
        sent_ids = {el.id for el in original_elements}
        received_ids = {el.id for el in translated_map.elements}
        
        if sent_ids != received_ids:
            missing = sent_ids - received_ids
            extra = received_ids - sent_ids
            raise TranslationValidationError(
                f"ID Mismatch. Missing: {missing}, Extra: {extra}"
            )

class CompositeValidator:
    """Orquestador que ejecuta múltiples validaciones."""
    def __init__(self, validators: list[TranslationValidator]):
        self.validators = validators

    def validate(self, original_elements: list[TranslationMapElement], translated_map: TranslationMap) -> None:
        for validator in self.validators:
            validator.validate(original_elements, translated_map)
