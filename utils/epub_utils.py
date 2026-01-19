from ebooklib import epub, ITEM_DOCUMENT
import tiktoken
from models.translation import TranslationMap

def load_epub_content(file_path: str) -> str:
    """Loads all document items from an EPUB and returns them as a single string."""
    book = epub.read_epub(file_path)
    return "\n".join([
        item.get_content().decode('utf-8') 
        for item in book.get_items() 
        if item.get_type() == ITEM_DOCUMENT
    ])

def count_map_tokens(translation_map: TranslationMap) -> int:
    """Calculates total estimated tokens for all elements in the map."""
    encoding = tiktoken.get_encoding("cl100k_base")
    total_tokens = 0
    for el in translation_map.elements:
        # We include ID and text for a realistic estimation
        content_to_encode = f"{el.id}: {el.text}"
        total_tokens += len(encoding.encode(content_to_encode))
    
    # 10% margin for JSON overhead and system prompt
    return int(total_tokens * 1.1)
