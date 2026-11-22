from src.optimizer import is_valid_outfit, optimize_outfits


def item(item_id, name, category, colour="#111111", season="All-season", occasion="Casual"):
    return {
        "id": item_id,
        "name": name,
        "category": category,
        "dominant_color": colour,
        "fabric": "Cotton",
        "season": season,
        "occasion": occasion,
        "embedding_json": '[1.0, 0.2, 0.1]',
        "image_path": f"data/processed/{name.lower().replace(' ', '_')}.jpg",
    }


def test_valid_outfit_structures():
    top = item(1, "White Shirt", "Shirt")
    bottom = item(2, "Black Jeans", "Jeans")
    shoes = item(3, "Black Shoes", "Shoes")
    dress = item(4, "Blue Dress", "Dress")
    jacket = item(5, "Warm Jacket", "Jacket")

    assert is_valid_outfit([top, bottom, shoes])
    assert is_valid_outfit([top, bottom, shoes, jacket])
    assert is_valid_outfit([dress, shoes])


def test_invalid_outfits_are_never_returned():
    two_tops = [
        item(1, "White Shirt", "Shirt"),
        item(2, "Blue Shirt", "Shirt"),
        item(3, "Black Shoes", "Shoes"),
    ]
    dress_and_pants = [
        item(4, "Blue Dress", "Dress"),
        item(5, "Black Pants", "Pants"),
        item(6, "Black Boots", "Boots"),
    ]

    assert not is_valid_outfit(two_tops)
    assert not is_valid_outfit(dress_and_pants)


def test_optimizer_generates_different_valid_outfits_and_limits_five():
    wardrobe = [
        item(1, "White Shirt", "Shirt", "#FFFFFF"),
        item(2, "Blue Shirt", "Shirt", "#336699"),
        item(3, "Black Jeans", "Jeans", "#111111"),
        item(4, "Blue Pants", "Pants", "#2244AA"),
        item(5, "White Sneakers", "Sneakers", "#FFFFFF"),
        item(6, "Black Boots", "Boots", "#111111"),
        item(7, "Blue Dress", "Dress", "#336699"),
        item(8, "Warm Jacket", "Jacket", "#222222", season="Winter"),
    ]

    outfits = optimize_outfits(
        wardrobe,
        occasion="Casual",
        weather={"temperature_c": 12, "rain": False, "condition": "Clear"},
        preferences={"preferred_categories": ["shirt", "jeans"], "preferred_fabrics": ["cotton"]},
        recently_worn_ids=[1, 5],
        top_n=5,
    )

    assert 1 <= len(outfits) <= 5
    keys = [tuple(sorted(outfit["item_ids"])) for outfit in outfits]
    assert len(keys) == len(set(keys))
    assert all(is_valid_outfit(outfit["items"]) for outfit in outfits)
