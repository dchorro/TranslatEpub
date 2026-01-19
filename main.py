from models.usage import UsageStatistics
from core.translator import OpenRouterClient
from core.epub_processor import EpubProcessor
from core.persistence import TranslationCache
from core.translation_service import TranslationService
from core.config import settings
from utils.epub_utils import load_epub_content, count_map_tokens
from models.translation import TranslationMap
import os
import logging

# Configuración de Logging para ver el flujo detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def translate_ebook_flow(target_language: str = "spanish", use_cache: bool = True):
    """Main business logic orchestration."""
    
    # 1. Initialization (Dependency Injection principle)
    cache = TranslationCache()
    session_stats = UsageStatistics()
    client = OpenRouterClient(api_key=settings.openrouter_api_key, stats=session_stats)
    client.fetch_model_prices()

    service = TranslationService(client, cache)
    processor = EpubProcessor()

    # 2. Data Loading
    # file_path = "reduced_2_first_chapter.html"
    # raw_html = load_reduced_first_chapter(file_path)
    
    file_path = "Dungeon_Crawler_Carl.epub"
    raw_html = load_epub_content(file_path)
    print(f"{len(raw_html)=}")
    logger.info(f"Starting process for {file_path}")

    import sys
    # 3. Execution Flow
    try:
        # Transformation
        skeleton, map_to_translate = processor.extract_structure(raw_html)
        logger.info(f"Extracted {len(map_to_translate.elements)} elements.")

        print(f"{len(map_to_translate.model_dump())=}")
        # print(f"{map_to_translate.model_dump()["elements"]=}")

        # import json
        # a = "\n\n\n".join(json.dumps(elem) for elem in map_to_translate.model_dump()["elements"][100:200])
        # print(a)
        # sys.exit(1)


        map_to_translate = TranslationMap(elements=map_to_translate.model_dump()["elements"][:200])

        total_tokens_to_translate = count_map_tokens(map_to_translate)
        logger.info(f"Sending {total_tokens_to_translate} tokens to LLM.")

        # To estimate the cost, we multiply tokens * 2 becuase of input and output tokens of LLM.
        logger.info(f"Escenario Económico (Gemini Flash): ${((total_tokens_to_translate * 2) / 1_000_000) * 0.10:.4f}")
        logger.info(f"Escenario Estándar (GPT-4o Mini):   ${((total_tokens_to_translate * 2) / 1_000_000) * 0.6:.4f}")
        logger.info(f"Escenario Premium  (GPT-4o/Claude):  ${((total_tokens_to_translate * 2) / 1_000_000) * 5:.4f}")
        # logger.info(f"Esimated cost of the translation ")


        translated_map = service.translate(
            book_id=file_path,
            to_translate=map_to_translate,
            target_lang=target_language,
            use_cache=use_cache
        )

        # Reconstruction
        final_html = processor.rebuild_html(skeleton, translated_map)
        
        # 4. Output
        with open("translated_chapter.html", "w", encoding="utf-8") as f:
            f.write(final_html)
        logger.info("Process finished successfully.")

        logger.info("\n" + "="*30)
        logger.info("RESUMEN DE CONSUMO")
        logger.info(f"Tokens Totales: {session_stats.total_tokens}")
        logger.info(f"Coste Estimado: ${session_stats.total_cost_usd}")
        logger.info("="*30)

    except Exception as e:
        logger.error(f"Process failed: {e}", exc_info=True)



if __name__ == "__main__":
    translate_ebook_flow(use_cache=True)