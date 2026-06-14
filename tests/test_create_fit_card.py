from tools import create_fit_card

SAMPLE_ITEM = {
    "id": "lst_006",
    "title": "Graphic Tee — 2003 Tour Bootleg Style",
    "description": "Vintage-style bootleg tee with faded graphic.",
    "category": "tops",
    "style_tags": ["graphic tee", "vintage", "grunge", "streetwear"],
    "size": "L",
    "condition": "good",
    "price": 24.0,
    "colors": ["black"],
    "brand": None,
    "platform": "depop"
}

SAMPLE_OUTFIT = (
    "Pair the graphic tee with baggy dark wash jeans and chunky white sneakers. "
    "Layer a vintage black denim jacket on top for a grunge-streetwear vibe."
)

def test_create_fit_card_normal():
    result = create_fit_card(SAMPLE_OUTFIT, SAMPLE_ITEM)
    print("\n--- create_fit_card NORMAL ---")
    print(result)
    assert isinstance(result, str)
    assert len(result) > 0

def test_create_fit_card_empty_outfit():
    result = create_fit_card("", SAMPLE_ITEM)
    print("\n--- create_fit_card EMPTY outfit ---")
    print(result)
    assert "Could not generate" in result

def test_create_fit_card_whitespace_outfit():
    result = create_fit_card("   ", SAMPLE_ITEM)
    print("\n--- create_fit_card WHITESPACE outfit ---")
    print(result)
    assert "Could not generate" in result
