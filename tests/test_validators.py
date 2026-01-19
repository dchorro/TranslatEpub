import pytest
from core.validators import IDAlignmentValidator, TranslationValidationError, CompositeValidator
from models.translation import TranslationMap, TranslationMapElement

def test_id_alignment_validator_success():
    validator = IDAlignmentValidator()
    original = [TranslationMapElement(id="REF_001", text="Hello")]
    translated = TranslationMap(elements=[TranslationMapElement(id="REF_001", text="Hola")])
    
    # No debería lanzar excepción
    validator.validate(original, translated)

def test_id_alignment_validator_mismatch():
    validator = IDAlignmentValidator()
    original = [TranslationMapElement(id="REF_001", text="Hello")]
    # El LLM devuelve un ID diferente
    translated = TranslationMap(elements=[TranslationMapElement(id="REF_999", text="Hola")])
    
    with pytest.raises(TranslationValidationError) as excinfo:
        validator.validate(original, translated)
    assert "ID Mismatch" in str(excinfo.value)

def test_composite_validator_execution():
    class SpyValidator:
        def __init__(self):
            self.called = False
        def validate(self, original, translated):
            self.called = True

    spy1 = SpyValidator()
    spy2 = SpyValidator()
    composite = CompositeValidator([spy1, spy2])
    
    composite.validate([], TranslationMap(elements=[]))
    
    assert spy1.called is True
    assert spy2.called is True
