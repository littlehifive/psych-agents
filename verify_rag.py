
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from theory_council.gemini_store import sync_all_theory_stores, get_theory_store_name
from theory_council.graph import get_gemini_agent
from theory_council.config import get_google_api_key

def test_sync_and_query():
    print("1. Syncing stores...")
    context_dir = os.path.join(os.getcwd(), "context")
    mapping = sync_all_theory_stores(context_dir)
    print(f"Mapping: {mapping}")
    
    print("\n2. Testing SDT Agent RAG...")
    sdt = get_gemini_agent("sdt")
    if not sdt.store_name:
        print("ERROR: SDT Agent has no store name!")
        return

    print(f"SDT Store: {sdt.store_name}")
    response = sdt.invoke([{"role": "user", "content": "What are the three basic psychological needs according to SDT?"}])
    print(f"SDT Response:\n{response.content}")
    
    print("\n3. Testing IM Anchor RAG...")
    im = get_gemini_agent("im_anchor")
    if not im.store_name:
         print("ERROR: IM Agent has no store name!")
         return
    print(f"IM Store: {im.store_name}")
    response = im.invoke([{"role": "user", "content": "What is Step 1 of Intervention Mapping?"}])
    print(f"IM Response:\n{response.content}")

if __name__ == "__main__":
    if not os.environ.get("GOOGLE_API_KEY"):
        print("GOOGLE_API_KEY not found.")
    else:
        test_sync_and_query()
