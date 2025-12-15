"""
Gemini File Search Store Manager.
Handles syncing local context files to a managed Gemini File Search Store.
"""
import logging
import os
import glob
import time
from typing import Optional

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

def get_or_create_store(client: genai.Client, display_name: str = "Theory Council Context") -> types.FileSearchStore:
    """
    Finds an existing File Search Store by display name or creates a new one.
    """
    logger.info("Checking for existing File Search Store: '%s'...", display_name)
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

def sync_context_files(context_dir: str, display_name: str = "Theory Council Context") -> Optional[str]:
    """
    Syncs all PDFs in the context_dir to the Gemini File Search Store.
    Returns the name (ID) of the store.
    """
    try:
        client = get_gemini_client()
        store = get_or_create_store(client, display_name)
        
        pdf_files = glob.glob(os.path.join(context_dir, "**/*.pdf"), recursive=True)
        if not pdf_files:
            logger.info("No PDFs found in %s to sync.", context_dir)
            return store.name

        logger.info("Found %d PDFs in context directory. Syncing to Gemini...", len(pdf_files))
        
        # In a real sync, we would check if files are already in the store.
        # But SDK doesn't offer easy 'list files in store' with filename filtering.
        # For this version, we will just upload.
        # Note: Creating a 'File' resource is separate from 'Importing' it to a store?
        # The user MD says: upload_file -> import_file OR use import_file directly?
        # User MD says: "upload existing file and import it"
        # sample_file = client.files.upload(file='sample.txt')
        # operation = client.file_search_stores.import_file(...)
        
        for file_path in pdf_files:
            filename = os.path.basename(file_path)
            logger.info("Processing %s...", filename)
            
            # 1. Upload File
            # We assume we upload a fresh copy every time for now (simplifies "sync" logic)
            # Ideally we check existence.
            uploaded_file = client.files.upload(file=file_path, config={'display_name': filename})
            logger.info("Uploaded file resource: %s", uploaded_file.name)
            
            # 2. Import into Store
            # This returns an operation
            operation = client.file_search_stores.import_file(
                file_search_store_name=store.name,
                file_name=uploaded_file.name
            )
            
            # Wait for completion? User MD shows while loop.
            # For batch uploads, waiting sequentially is slow but safe.
            while not operation.done:
                time.sleep(1)
                operation = client.operations.get(name=operation.name)
                
            logger.info("Import complete for %s", filename)

        logger.info("Sync complete. Store ready: %s", store.name)
        return store.name
    
    except Exception as e:
        logger.error("Failed to sync Gemini store: %s", e)
        return None
