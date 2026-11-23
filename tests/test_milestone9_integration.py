from src.auth import authenticate_user, register_user
from src.database import (
    get_outfit_feedback,
    get_outfit_history,
    initialize_database,
    record_outfit_feedback,
    record_outfit_worn,
)


def test_auth_registration_and_login(tmp_path):
    db_path = tmp_path / "milestone9.db"
    initialize_database(db_path)

    user = register_user("Alex Style", "alex@example.com", "strongpass", db_path)
    assert user["email"] == "alex@example.com"
    assert authenticate_user("alex@example.com", "strongpass", db_path)["id"] == user["id"]
    assert authenticate_user("alex@example.com", "wrongpass", db_path) is None


def test_feedback_and_wear_history(tmp_path):
    db_path = tmp_path / "milestone9.db"
    initialize_database(db_path)
    user = register_user("Sam User", "sam@example.com", "strongpass", db_path)

    record_outfit_worn(db_path, user["id"], [3, 1, 2])
    history = get_outfit_history(db_path, user["id"])
    assert len(history) == 1
    assert set(history[0]["item_ids"]) == {1, 2, 3}

    record_outfit_feedback(db_path, user["id"], [3, 1, 2], 5, "Great outfit")
    record_outfit_feedback(db_path, user["id"], [3, 1, 2], 4, "Updated rating")
    feedback = get_outfit_feedback(db_path, user["id"])
    assert len(feedback) == 1
    assert feedback[0]["rating"] == 4
    assert feedback[0]["comment"] == "Updated rating"
