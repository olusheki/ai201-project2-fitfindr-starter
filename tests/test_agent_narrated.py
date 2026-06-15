"""
Narrated walkthrough of the FitFindr agent loop.
Shows each step, what's being passed between tools, and the final output.
Run with: .venv/bin/python tests/test_agent_narrated.py
"""

import json
from tools import search_listings, suggest_outfit, create_fit_card, _get_groq_client
from utils.data_loader import get_example_wardrobe, load_listings

DIVIDER = "-" * 60


def score_items(description, results):
    """Re-score results so we can display scores alongside titles."""
    keywords = description.lower().split()
    scored = []
    for item in results:
        searchable = (
            item["description"].lower().split()
            + item["style_tags"]
            + item["title"].lower().split()
            + item["category"].lower().split()
        )
        score = sum(1 for word in keywords if word in searchable)
        scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def run_narrated(query, wardrobe, label):
    print(f"\n{'=' * 60}")
    print(f"SCENARIO: {label}")
    print(f"{'=' * 60}")
    print(f"User query: \"{query}\"")

    # Step 2: Parse query
    print(f"\n{DIVIDER}")
    print("STEP 2 — Parsing query with LLM")
    client = _get_groq_client()
    prompt = f"""Extract search parameters from this clothing query. Respond with ONLY a JSON object, no explanation.

Query: "{query}"

Return this exact format:
{{
  "description": "short phrase describing the clothing item and style (e.g. 'vintage graphic tee')",
  "size": "size string if mentioned (e.g. 'M', 'S/M', 'XL'), or null if not mentioned",
  "max_price": numeric price ceiling if mentioned (e.g. 30.0), or null if not mentioned
}}"""
    print(f"Prompt sent to LLM:\n{prompt}")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = response.choices[0].message.content
    print(f"\nLLM raw response: {raw}")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        print("ERROR: Could not parse LLM response as JSON. Stopping.")
        return

    print(f"\nParsed parameters:")
    print(f"  description : {parsed['description']}")
    print(f"  size        : {parsed['size']}")
    print(f"  max_price   : {parsed['max_price']}")

    # Step 3: Search listings
    print(f"\n{DIVIDER}")
    print(f"STEP 3 — Calling search_listings(description=\"{parsed['description']}\", size={parsed['size']}, max_price={parsed['max_price']})")
    results = search_listings(parsed["description"], parsed["size"], parsed["max_price"])

    if not results and (parsed.get("size") or parsed.get("max_price")):
        print("No results with original constraints. Retrying with description only (dropping size and max_price)...")
        results = search_listings(parsed["description"], None, None)
        if results:
            print(f"Retry succeeded! Telling user: 'No exact matches found with your size/price constraints. I loosened the search and found these instead.'")
        else:
            print("Retry also returned no results. Stopping early.")
            print("Error returned to user: Sorry, I couldn't find any items that matched your description even after loosening size and price constraints.")
            return
    elif not results:
        print("No results found. Stopping early.")
        print("Error returned to user: Sorry, I couldn't find any items that matched your description.")
        return

    scored = score_items(parsed["description"], results)
    top3 = scored[:3]
    print(f"\nTop {len(top3)} result(s) by relevance score:")
    for i, (score, item) in enumerate(top3, 1):
        print(f"  {i}. [{score} pts] {item['title']} — ${item['price']:.2f} ({item['platform']})")

    # Step 4: Select top item
    print(f"\n{DIVIDER}")
    print("STEP 4 — Selecting top item")
    selected = results[0]
    print(f"  → Passing to suggest_outfit: \"{selected['title']}\"")

    # Step 5: Suggest outfit
    print(f"\n{DIVIDER}")
    wardrobe_items = wardrobe["items"]
    if wardrobe_items:
        print(f"STEP 5 — Calling suggest_outfit with item + wardrobe ({len(wardrobe_items)} pieces)")
        wardrobe_preview = [item["name"] for item in wardrobe_items[:3]]
        print(f"  Wardrobe sample: {wardrobe_preview} ...")
    else:
        print("STEP 5 — Calling suggest_outfit with item + EMPTY wardrobe (general advice mode)")

    outfit = suggest_outfit(selected, wardrobe)
    print(f"\noutfit_suggestion:\n{outfit}")

    # Step 6: Create fit card
    print(f"\n{DIVIDER}")
    print(f"STEP 6 — Calling create_fit_card")
    print(f"  Passing outfit_suggestion (first 80 chars): \"{outfit[:80]}...\"")
    print(f"  Passing item: \"{selected['title']}\" — ${selected['price']:.2f} on {selected['platform']}")

    fit_card = create_fit_card(outfit, selected)
    print(f"\nfit_card:\n{fit_card}")

    print(f"\n{DIVIDER}")
    print("DONE — session state summary:")
    print(f"  selected_item     : {selected['title']}")
    print(f"  outfit_suggestion : {outfit[:60]}...")
    print(f"  fit_card          : {fit_card[:60]}...")
    print(f"  error             : None")


if __name__ == "__main__":
    wardrobe = get_example_wardrobe()

    run_narrated(
        query="looking for a vintage graphic tee under $30",
        wardrobe=wardrobe,
        label="Happy path — vintage graphic tee",
    )

    run_narrated(
        query="designer ballgown size XXS under $5",
        wardrobe=wardrobe,
        label="Error path — no results expected (total failure)",
    )

    run_narrated(
        query="looking for a graphic tee size XXS under $5",
        wardrobe=wardrobe,
        label="Retry path — tight constraints loosened automatically",
    )
