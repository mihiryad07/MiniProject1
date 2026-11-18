import sqlite3

from src.database import (
    add_wardrobe_item,
    delete_wardrobe_item,
    get_or_create_default_user,
    get_wardrobe_items,
    initialize_database,
    update_wardrobe_item,
)


def test_database_crud_operations(tmp_path):
    db_path = tmp_path / "wardrobe.db"
    initialize_database(db_path)

    connection = sqlite3.connect(db_path)
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    connection.close()

    assert "users" in tables
    assert "wardrobe_items" in tables

    user_id = get_or_create_default_user(db_path)
    item_id = add_wardrobe_item(
        db_path,
        {
            "user_id": user_id,
            "name": "Blue Shirt",
            "category": "Shirt",
            "image_path": "data/processed/blue_shirt.jpg",
            "dominant_color": "#0000FF",
            "fabric": "Cotton",
            "season": "Summer",
            "occasion": "Casual",
        },
    )

    items = get_wardrobe_items(db_path, user_id)
    assert len(items) == 1
    assert items[0]["id"] == item_id
    assert items[0]["dominant_color"] == "#0000FF"

    assert update_wardrobe_item(
        db_path,
        item_id,
        {"occasion": "Formal", "fabric": "Linen"},
    )

    updated_items = get_wardrobe_items(db_path, user_id)
    assert updated_items[0]["occasion"] == "Formal"
    assert updated_items[0]["fabric"] == "Linen"

    assert delete_wardrobe_item(db_path, item_id)
    assert get_wardrobe_items(db_path, user_id) == []
