"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

from tools import search_listings, suggest_outfit, create_fit_card, _get_groq_client
import json

# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
        "retry_note": None,          # set if search was retried with loosened constraints
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    # TODO: implement the planning loop

    # Step 1: initalize a new session
    session = _new_session(query, wardrobe)

    #Step 2, parse the query to find a description of what item they're looking for
    # possible paths: ask an LLM, or extract key words. I'll probably ask an LLM.
    client = _get_groq_client()
    prompt = f"""Extract search parameters from this clothing query. Respond with ONLY a JSON object, no explanation.

    Query: "{query}"

    Return this exact format:
    {{
    "description": "short phrase describing the clothing item and style (e.g. 'vintage graphic tee')",
    "size": "size string if mentioned (e.g. 'M', 'S/M', 'XL'), or null if not mentioned",
    "max_price": numeric price ceiling if mentioned (e.g. 30.0), or null if not mentioned
    }}"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    try:
        parsed = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        session["error"] = "Failed to parse your query. Please try rephrasing it."
        return session

    session["parsed"] = parsed

    # Step 3
    relevant_clothes = search_listings(parsed["description"], parsed["size"], parsed["max_price"])
    if not relevant_clothes and (parsed.get("size") or parsed.get("max_price")):
        # Retry with loosened constraints — drop size and price ceiling
        relevant_clothes = search_listings(parsed["description"], None, None)
        if relevant_clothes:
            session["retry_note"] = (
                "No exact matches found with your size/price constraints. "
                "I loosened the search and found these instead."
            )
        else:
            session["error"] = (
                "Sorry, I couldn't find any items that matched your description "
                "even after loosening size and price constraints. "
                "Please try a different description."
            )
            return session
    elif not relevant_clothes:
        session["error"] = "Sorry, I couldn't find any items that matched your description. Please try again or ask for something else."
        return session

    session["search_results"] = relevant_clothes

    # Step 4
    top_item = relevant_clothes[0]
    session["selected_item"] = top_item

    # Step 5
    session["outfit_suggestion"] = suggest_outfit(top_item, session["wardrobe"])

    # Step 6
    session["fit_card"] = create_fit_card(session["outfit_suggestion"], top_item)

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
