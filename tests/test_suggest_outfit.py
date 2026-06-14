from tools import suggest_outfit
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

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

def test_suggest_outfit_with_wardrobe():
    wardrobe = get_example_wardrobe()
    result = suggest_outfit(SAMPLE_ITEM, wardrobe)
    print("\n--- suggest_outfit WITH wardrobe ---")
    print(result)
    assert isinstance(result, str)
    assert len(result) > 0

def test_suggest_outfit_empty_wardrobe():
    wardrobe = get_empty_wardrobe()
    result = suggest_outfit(SAMPLE_ITEM, wardrobe)
    print("\n--- suggest_outfit EMPTY wardrobe ---")
    print(result)
    assert isinstance(result, str)
    assert len(result) > 0
