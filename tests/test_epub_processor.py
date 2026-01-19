import pytest
from core.epub_processor import EpubProcessor
from models.translation import TranslationMap, TranslationMapElement
from bs4 import BeautifulSoup

def test_extract_structure_replaces_tags_with_placeholders():
    processor = EpubProcessor()
    html = "<div><h1>Title</h1><p>Paragraph 1</p><p></p></div>"
    
    skeleton, translation_map = processor.extract_structure(html)
    
    # 1. Verificar que ha extraído los elementos con texto
    assert len(translation_map.elements) == 2
    assert translation_map.elements[0].text == "Title"
    assert translation_map.elements[1].text == "Paragraph 1"
    
    # 2. Verificar que el esqueleto tiene los placeholders
    assert "REF_000001" in str(skeleton)
    assert "REF_000002" in str(skeleton)
    # El tag vacío no debería generar un elemento de traducción
    assert "REF_000003" not in str(skeleton)

def test_rebuild_html_restores_content():
    processor = EpubProcessor()
    original_html = "<html><body><h1>Original Title</h1></body></html>"
    
    # Extraer
    skeleton, translation_map = processor.extract_structure(original_html)
    
    # Simular traducción
    translated_elements = [
        TranslationMapElement(id="REF_000001", text="Título Traducido")
    ]
    translated_map = TranslationMap(elements=translated_elements)
    
    # Reconstruir
    final_html = processor.rebuild_html(skeleton, translated_map)
    
    # Verificar
    assert "<h1>Título Traducido</h1>" in final_html
    assert "Original Title" not in final_html

def test_extract_structure_preserves_inner_html_tags():
    """Verifica que mantenemos etiquetas de formato como <i> o <b> dentro del texto."""
    processor = EpubProcessor()
    html = "<p>Text with <i>italics</i> and <b>bold</b>.</p>"
    
    _, translation_map = processor.extract_structure(html)
    
    assert translation_map.elements[0].text == "Text with <i>italics</i> and <b>bold</b>."
