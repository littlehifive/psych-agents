
import asyncio
import os
import sys
from typing import List

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src")))

from theory_council.chat import generate_chat_response, astream_chat_response, organize_library_item

async def verify_usage():
    print("--- Verifying Sync Chat Usage ---")
    messages = [{"role": "user", "content": "Tell me a short joke about psychology."}]
    result = generate_chat_response(messages)
    print(f"Model: {result.get('model')}")
    print(f"Usage: {result.get('usage')}")
    if result.get('usage'):
        print("✅ Sync usage captured.")
    else:
        print("❌ Sync usage MISSING.")

    print("\n--- Verifying Streaming Chat Usage ---")
    full_text = ""
    async for chunk in astream_chat_response(messages):
        full_text += chunk
    print(f"Stream response: {full_text[:50]}...")
    print("Note: Streaming usage is reported via get_current_run_tree().end(), which we can't easily check here without mocking langsmith, but the code path was executed.")

    print("\n--- Verifying Library Organizer Usage ---")
    org_result = organize_library_item(
        "What is SCT?",
        "Social Cognitive Theory (SCT) describes the influence of individual experiences, the actions of others, and environmental factors on individual health behaviors."
    )
    print(f"Title: {org_result.get('title')}")
    print(f"Usage: {org_result.get('_usage')}")
    if org_result.get('_usage'):
        print("✅ Library organization usage captured.")
    else:
        print("❌ Library organization usage MISSING.")

if __name__ == "__main__":
    asyncio.run(verify_usage())
