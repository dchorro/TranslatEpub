from bs4 import BeautifulSoup
from models.translation import TranslationMapElement, TranslationMap
from core.config import settings


class EpubProcessor:
    def __init__(self):
        self.placeholder_fmt = settings.placeholder_fmt
        self.target_tags = settings.target_tags

    def extract_structure(self, html_content: str) -> tuple[BeautifulSoup, TranslationMap]:
        """
        Deconstructs HTML into a skeleton and a Pydantic model for translation.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        elements = []
        counter = 1

        for tag in soup.find_all(self.target_tags):
            # We check if it has actual text to avoid translating empty tags
            if tag.get_text(strip=True):
                ref_id = self.placeholder_fmt.format(counter)
                
                # Create the Pydantic element
                element = TranslationMapElement(
                    id=ref_id,
                    text=tag.decode_contents().strip()
                )
                elements.append(element)
                
                # Replace content with ID in the skeleton
                tag.string = ref_id
                counter += 1

        return soup, TranslationMap(elements=elements)

    def rebuild_html(self, skeleton: BeautifulSoup, translated: TranslationMap) -> str:
        """
        Reconstructs the HTML by mapping IDs back to translated text.
        """
        # Mapping for O(1) lookup during reconstruction
        translation_lookup = {el.id: el.text for el in translated.elements}

        # We find all text nodes that match our placeholder pattern
        for ref_id, translated_text in translation_lookup.items():
            node = skeleton.find(string=ref_id)
            if node:
                # Parse translated text back to HTML nodes
                new_content = BeautifulSoup(translated_text, 'html.parser')
                node.replace_with(new_content)
        
        return skeleton.encode(formatter="minimal").decode('utf-8')