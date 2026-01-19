import pytest
import requests
from unittest.mock import MagicMock, patch
from core.translator import OpenRouterClient
from core.validators import TranslationValidationError
from models.translation import TranslationMap, TranslationMapElement
from models.usage import UsageStatistics

@pytest.fixture
def mock_stats():
    return UsageStatistics()

@pytest.fixture
def client(mock_stats):
    return OpenRouterClient(api_key="fake_key", stats=mock_stats)

def test_client_calls_validator_and_retries_on_validation_error(client):
    """Verifica que el cliente llama al validador y que Tenacity reintenta si falla."""
    
    # 1. Setup mocks
    mock_validator = MagicMock()
    # Forzamos un fallo en el primer intento y éxito en el segundo
    mock_validator.validate.side_effect = [
        TranslationValidationError("Mock Error"),
        None # Success
    ]
    client.validator = mock_validator
    
    batch = [TranslationMapElement(id="REF_001", text="Hello")]
    
    # Mock de la respuesta de requests.post
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"elements": [{"id": "REF_001", "text": "Hola"}]}'}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10}
    }

    with patch('requests.post', return_value=mock_response) as mock_post:
        # 2. Execute
        results = client._send_request(batch, "system prompt")
        
        # 3. Verify
        assert len(results) == 1
        assert results[0].text == "Hola"
        # Tenacity debería haber reintentado, por lo que post y validate se llaman 2 veces
        assert mock_post.call_count == 2
        assert mock_validator.validate.call_count == 2
