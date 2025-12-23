"""
Gemini File Search Store Manager.
Handles syncing local context files to a managed Gemini File Search Store.
"""
import logging
import os
import glob
import time
from typing import Optional, Dict

from google import genai
from google.genai import types

from .config import get_google_api_key

logger = logging.getLogger("theory_council.gemini_store")

def get_gemini_client() -> genai.Client:
    """
    Construct a Gemini Client using the project configuration.
    """
    api_key = get_google_api_key()
    return genai.Client(api_key=api_key)

def get_or_create_store(client: genai.Client, display_name: str) -> types.FileSearchStore:
    """
    Finds an existing File Search Store by display name or creates a new one.
    """
    # logger.info("Checking for existing File Search Store: '%s'...", display_name)
    try:
        # Note: listing might be paginated, for this demo we scan the first page/batch
        # SDK 1.55.0 usage
        for store in client.file_search_stores.list():
            if store.display_name == display_name:
                logger.info("Found existing store: %s", store.name)
                return store
    except Exception as e:
        logger.warning("Failed to list stores: %s", e)

    # Create if not found
    logger.info("Creating new File Search Store: '%s'...", display_name)
    new_store = client.file_search_stores.create(config={'display_name': display_name})
    logger.info("Created store: %s", new_store.name)
    return new_store

def sync_context_files(source_dir: str, display_name: str) -> Optional[str]:
    """
    Syncs all PDFs in the source_dir to a specific Gemini File Search Store.
    Returns the name (ID) of the store.
    """
    try:
        if not os.path.exists(source_dir):
            logger.warning("Directory not found: %s", source_dir)
            return None

        client = get_gemini_client()
        store = get_or_create_store(client, display_name)
        
        pdf_files = glob.glob(os.path.join(source_dir, "**/*.pdf"), recursive=True)
        if not pdf_files:
            logger.info("No PDFs found in %s to sync.", source_dir)
            return store.name
            
        logger.info("Syncing %d PDFs from '%s' to store '%s'...", len(pdf_files), source_dir, display_name)
        
        for file_path in pdf_files:
            filename = os.path.basename(file_path)
            # Simplistic check: just upload. In prod, check if hash exists or similar.
            # logger.info("Processing %s...", filename)
            
            # 1. Upload File
            uploaded_file = client.files.upload(file=file_path, config={'display_name': filename})
            # logger.info("Uploaded file resource: %s", uploaded_file.name)
            
            # 2. Import into Store
            operation = client.file_search_stores.import_file(
                file_search_store_name=store.name,
                file_name=uploaded_file.name
            )
            
            # Debug print
            # logger.info("Operation type: %s", type(operation))
            while not operation.done:
                time.sleep(2)
                # logger.info("Refreshing operation: %s", operation.name)
                # Pass the operation object itself if the SDK expects an object with .name
                operation = client.operations.get(operation)

        logger.info("Sync complete for store: %s", display_name)
        return store.name
    
    except Exception as e:
        logger.exception("Sync failed for %s", display_name)
        return None


# Global cache of theory key -> store name
_THEORY_STORE_MAPPING: Dict[str, str] = {}

def get_theory_store_name(theory_key: str) -> Optional[str]:
    return _THEORY_STORE_MAPPING.get(theory_key)

def sync_all_theory_stores(base_context_dir: str) -> Dict[str, str]:
    """
    Syncs the 5 theory folders + generic context to their respective stores.
    Returns a dict mapping {theory_key: store_name}.
    """
    # Map subdirectory -> (Theory Key, Display Name)
    mapping = {
        "Intervention Mapping": ("im_anchor", "Theory Council - IM"),
        "Social Cognitive Theory": ("sct", "Theory Council - SCT"),
        "Self Determination Theory": ("sdt", "Theory Council - SDT"),
        "Wise Intervention": ("wise", "Theory Council - Wise"),
        "Theory of Planned Behavior": ("ra", "Theory Council - RA"),
        "Ecological Theories & Implementation Science": ("env_impl", "Theory Council - EnvImpl"),
    }
    
    results = {}
    for sub, (key, name) in mapping.items():
        dir_path = os.path.join(base_context_dir, sub)
        store_name = sync_context_files(dir_path, name)
        if store_name:
            results[key] = store_name
            # Update global cache
            _THEORY_STORE_MAPPING[key] = store_name

    logger.info("All theory stores synced: %s", results)
    return results
