from src.recommendation import (
    calculate_similarity,
    colour_score,
    generate_outfit_combinations,
)


def make_item(item_id, name, category, colour, embedding, occasion="Casual"):
    return {
        "id": item_id,
        "name": name,
        "category": category,
        "dominant_color": colour,
        "embedding_json": __import__("json").dumps(embedding),
        "occasion": occasion,
        "image_path": f"data/processed/{name.lower().replace(' ', '_')}.jpg",
    }


def test_similarity_combines_embedding_colour_and_category():
    shirt = make_item(1, "Blue Shirt", "Shirt", "#336699", [1.0, 0.2, 0.1])
    pants = make_item(2, "Black Jeans", "Jeans", "#111111", [0.9, 0.3, 0.2])

    scores = calculate_similarity(shirt, pants)

    assert 0.0 <= scores["embedding_similarity"] <= 1.0
    assert 0.0 <= scores["texture_similarity"] <= 1.0
    assert 0.0 <= scores["colour_compatibility"] <= 1.0
    assert scores["category_compatibility"] == 1.0
    assert 0.0 <= scores["combined_score"] <= 1.0


def test_colour_compatibility_accepts_neutral_colours():
    assert colour_score("#000000", "#336699") >= 0.8
    assert 0.0 <= colour_score("#FFFFFF", "#FF0000") <= 1.0


def test_generate_outfit_combinations_returns_ranked_top_five():
    wardrobe = [
        make_item(1, "Blue Shirt", "Shirt", "#336699", [1.0, 0.2, 0.1]),
        make_item(2, "White Shirt", "Shirt", "#FFFFFF", [0.8, 0.3, 0.2]),
        make_item(3, "Black Jeans", "Jeans", "#111111", [0.9, 0.2, 0.1]),
        make_item(4, "Blue Pants", "Pants", "#2244AA", [0.7, 0.4, 0.2]),
        make_item(5, "White Sneakers", "Shoes", "#FFFFFF", [0.6, 0.5, 0.3]),
        make_item(6, "Black Boots", "Shoes", "#111111", [0.5, 0.4, 0.4]),
    ]

    outfits = generate_outfit_combinations(wardrobe, top_n=5)

    assert len(outfits) <= 5
    assert len(outfits) > 0
    assert all(set(outfit) >= {"items", "score", "item_ids", "reason"} for outfit in outfits)
    assert outfits == sorted(outfits, key=lambda outfit: outfit["score"], reverse=True)
