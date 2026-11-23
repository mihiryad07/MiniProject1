"""Streamlit pages for the Milestone 9 integrated application."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from src.auth import authenticate_user, register_user
from src.database import (
    DATABASE_PATH,
    get_outfit_feedback,
    get_outfit_history,
    get_recently_worn_item_ids,
    record_outfit_feedback,
    record_outfit_worn,
    get_or_create_default_user,
)
from src.recommendation import generate_outfit_combinations
from src.wardrobe import add_clothing_item, delete_clothing_item, list_clothing_items, update_clothing_item
from src.weather import WeatherAPIError, fetch_current_weather, manual_weather, weather_clothing_advice


def get_current_user_id() -> int:
    user = st.session_state.get("current_user")
    if user:
        return int(user["id"])
    return get_or_create_default_user(DATABASE_PATH)


def render_home() -> None:
    user = st.session_state.get("current_user")
    items = list_clothing_items(DATABASE_PATH, get_current_user_id())
    history = get_outfit_history(DATABASE_PATH, get_current_user_id())
    st.markdown("## Welcome to your digital wardrobe")
    st.write("Plan complete outfits, check the weather, and build a wardrobe that works together.")
    if user:
        st.success(f"Signed in as {user['name']}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Wardrobe items", len(items))
    c2.metric("Outfits worn", len(history))
    c3.metric("Recommendations", len(st.session_state.get("recommendations", [])))

    st.markdown("### Quick start")
    q1, q2, q3 = st.columns(3)
    q1.info("1. Upload your clothing\n\nAdd clear images and metadata.")
    q2.info("2. Set the weather\n\nChoose an occasion and weather source.")
    q3.info("3. Choose an outfit\n\nReview, wear, and rate your top five.")


def render_auth() -> None:
    st.markdown("## Account")
    login_tab, register_tab = st.tabs(["Login", "Registration"])
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", type="primary")
        if submitted:
            user = authenticate_user(email, password, DATABASE_PATH)
            if user:
                st.session_state["current_user"] = user
                st.session_state["recommendations"] = []
                st.success(f"Welcome, {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with register_tab:
        with st.form("registration_form"):
            name = st.text_input("Name")
            email = st.text_input("Email address")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account", type="primary")
        if submitted:
            if password != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    user = register_user(name, email, password, DATABASE_PATH)
                    st.session_state["current_user"] = user
                    st.success("Account created and logged in.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    if st.session_state.get("current_user"):
        if st.button("Logout"):
            st.session_state.pop("current_user", None)
            st.session_state["recommendations"] = []
            st.rerun()


def render_upload() -> None:
    st.markdown("## Upload wardrobe item")
    with st.form("milestone9_upload", clear_on_submit=True):
        uploaded = st.file_uploader("Clothing image", type=["png", "jpg", "jpeg", "webp"])
        name = st.text_input("Item name")
        c1, c2 = st.columns(2)
        category = c1.selectbox("Category", ["T-shirt", "Shirt", "Pants", "Jeans", "Dress", "Skirt", "Jacket", "Hoodie", "Sweater", "Shoes", "Sneakers", "Boots", "Sandals", "Accessory", "Other"])
        fabric = c2.selectbox("Fabric", ["Cotton", "Polyester", "Wool", "Silk", "Denim", "Linen", "Leather", "Other"])
        c3, c4 = st.columns(2)
        season = c3.selectbox("Season", ["Summer", "Winter", "Spring", "Autumn", "All-season"])
        occasion = c4.selectbox("Occasion", ["Casual", "Formal", "Party", "Sports", "Business", "Beach", "Other"])
        submitted = st.form_submit_button("Add clothing", type="primary")

    if submitted:
        if uploaded is None:
            st.error("Please upload an image.")
        elif not name.strip():
            st.error("Please enter an item name.")
        else:
            try:
                item = add_clothing_item(uploaded, name, category, fabric, season, occasion, DATABASE_PATH, get_current_user_id())
                st.success(f"Added {item['name']} ({item['dominant_color']}).")
                st.image(item["image_path"], caption=item["name"], use_container_width=True)
            except Exception as exc:
                st.error(f"Could not add clothing item: {exc}")


def render_wardrobe() -> None:
    st.markdown("## My wardrobe")
    items = list_clothing_items(DATABASE_PATH, get_current_user_id())
    if not items:
        st.info("Your wardrobe is empty. Use Upload Wardrobe to add your first item.")
        return

    search = st.text_input("Search items", placeholder="Name or category")
    filtered = [item for item in items if search.lower() in f"{item['name']} {item['category']}".lower()] if search else items
    columns = st.columns(3)
    for index, item in enumerate(filtered):
        with columns[index % 3]:
            if item.get("image_path") and Path(item["image_path"]).exists():
                st.image(item["image_path"], use_container_width=True)
            st.markdown(f"**{item['name']}**")
            st.caption(f"{item['category']} • {item['fabric'] or 'Fabric not set'}")
            st.caption(f"{item['season'] or 'Season not set'} • {item['occasion'] or 'Occasion not set'}")

    st.divider()
    c1, c2 = st.columns(2)
    selected_id = c1.selectbox("Select item", [item["id"] for item in items], format_func=lambda item_id: next(item["name"] for item in items if item["id"] == item_id))
    action = c2.selectbox("Action", ["Update", "Delete"])
    selected = next(item for item in items if item["id"] == selected_id)
    if action == "Update":
        name = st.text_input("Name", value=selected["name"], key="wardrobe_update_name")
        category = st.text_input("Category", value=selected["category"], key="wardrobe_update_category")
        fabric = st.text_input("Fabric", value=selected["fabric"] or "", key="wardrobe_update_fabric")
        season = st.text_input("Season", value=selected["season"] or "", key="wardrobe_update_season")
        occasion = st.text_input("Occasion", value=selected["occasion"] or "", key="wardrobe_update_occasion")
        if st.button("Save changes", type="primary"):
            update_clothing_item(selected_id, {"name": name.strip(), "category": category.strip(), "fabric": fabric.strip(), "season": season.strip(), "occasion": occasion.strip()}, DATABASE_PATH)
            st.success("Item updated.")
            st.rerun()
    else:
        st.warning("Deleting removes this item from the wardrobe.")
        if st.button("Delete selected item", type="primary"):
            delete_clothing_item(selected_id, DATABASE_PATH)
            st.success("Item deleted.")
            st.rerun()


def render_weather_occasion() -> None:
    st.markdown("## Weather and occasion")
    mode = st.radio("Weather source", ["OpenWeather API", "Manual weather"], horizontal=True)
    if mode == "OpenWeather API":
        city = st.text_input("City", value=st.session_state.get("weather_city", "Mumbai"))
        if st.button("Fetch weather", type="primary"):
            try:
                weather = fetch_current_weather(city)
                st.session_state["current_weather"] = weather
                st.session_state["weather_city"] = city
                st.success("Weather updated.")
            except WeatherAPIError as exc:
                st.error(str(exc))
    else:
        temperature = st.number_input("Temperature (°C)", -50.0, 60.0, 20.0, 1.0)
        condition = st.selectbox("Condition", ["Clear", "Clouds", "Rain", "Drizzle", "Thunderstorm", "Snow", "Fog"])
        raining = st.checkbox("Raining")
        if st.button("Use manual weather", type="primary"):
            st.session_state["current_weather"] = manual_weather(temperature, condition, raining)

    weather = st.session_state.get("current_weather")
    if weather:
        advice = weather_clothing_advice(weather)
        st.metric("Temperature", f"{weather['temperature_c']:.1f} °C", weather["description"])
        st.success(f"Season: {advice['season']} — {advice['advice']}")

    occasion = st.selectbox("Occasion", ["Any", "Casual", "Formal", "Party", "Sports", "Business", "Beach"])
    st.session_state["occasion"] = None if occasion == "Any" else occasion

    st.markdown("### Personal preferences")
    items = list_clothing_items(DATABASE_PATH, get_current_user_id())
    categories = sorted({str(i.get("category", "")).strip().lower() for i in items if i.get("category")})
    fabrics = sorted({str(i.get("fabric", "")).strip().lower() for i in items if i.get("fabric")})
    preferred_categories = st.multiselect("Preferred categories", categories)
    preferred_fabrics = st.multiselect("Preferred fabrics", fabrics)
    colours = st.text_input("Preferred hex colours", placeholder="#111111, #FFFFFF")
    st.session_state["preferences"] = {
        "preferred_categories": preferred_categories,
        "preferred_fabrics": preferred_fabrics,
        "preferred_colours": [value.strip().upper() for value in colours.split(",") if value.strip()],
    }


def _outfit_images(outfit: Dict[str, Any]) -> None:
    columns = st.columns(len(outfit["items"]))
    for column, item in zip(columns, outfit["items"]):
        with column:
            if item.get("image_path") and Path(item["image_path"]).exists():
                st.image(item["image_path"], use_container_width=True)
            st.caption(f"**{item['name']}**")
            st.caption(f"{item['category']} • {item.get('dominant_color') or 'No colour'}")


def render_recommendations() -> None:
    st.markdown("## Outfit recommendations")
    items = list_clothing_items(DATABASE_PATH, get_current_user_id())
    if len(items) < 3:
        st.info("Add at least three compatible wardrobe items to generate recommendations.")
        return

    if st.button("Generate top 5 outfits", type="primary"):
        recommendations = generate_outfit_combinations(
            items,
            occasion=st.session_state.get("occasion"),
            top_n=5,
            weather=st.session_state.get("current_weather"),
            preferences=st.session_state.get("preferences", {}),
            recently_worn_ids=get_recently_worn_item_ids(DATABASE_PATH, get_current_user_id(), limit=10),
        )
        st.session_state["recommendations"] = recommendations

    recommendations = st.session_state.get("recommendations", [])
    if not recommendations:
        st.info("No outfits generated yet. Configure weather and occasion, then generate recommendations.")
        return

    for rank, outfit in enumerate(recommendations, start=1):
        with st.container(border=True):
            st.markdown(f"### {rank}. {outfit['reason']}")
            a, b, c = st.columns(3)
            a.metric("Overall score", f"{outfit['score']:.2f}")
            b.metric("Compatibility", f"{outfit.get('compatibility_probability', 0.5):.0%}")
            c.metric("Weather suitability", f"{outfit.get('weather_suitability', 0.5):.0%}")
            _outfit_images(outfit)
            st.write(f"**Why:** {outfit['reason']} • style, weather, occasion, preferences and repetition are considered.")
            b1, b2 = st.columns(2)
            if b1.button("View details", key=f"details_{rank}"):
                st.session_state["selected_outfit"] = outfit
                st.session_state["requested_page"] = "Outfit Details"
                st.rerun()
            if b2.button("Mark as worn", key=f"worn_{rank}"):
                record_outfit_worn(DATABASE_PATH, get_current_user_id(), outfit["item_ids"])
                st.success("Saved to your wear history.")


def render_outfit_details() -> None:
    st.markdown("## Outfit details")
    outfit = st.session_state.get("selected_outfit")
    if not outfit:
        st.info("Select an outfit from Recommendations to view its details.")
        return

    st.markdown(f"### {outfit['reason']}")
    _outfit_images(outfit)
    c1, c2, c3 = st.columns(3)
    c1.metric("Compatibility", f"{outfit.get('compatibility_probability', 0.5):.0%}")
    c2.metric("Weather", f"{outfit.get('weather_suitability', 0.5):.0%}")
    c3.metric("Overall", f"{outfit['score']:.2f}")

    st.markdown("### Recommendation explanation")
    st.write(f"The outfit is valid and balanced as **{outfit['reason']}**.")
    st.write("It combines style compatibility, weather suitability, occasion fit, preferences, and a penalty for recently worn items.")

    st.markdown("### Item breakdown")
    for item in outfit["items"]:
        st.write(f"- **{item['name']}** — {item['category']}, {item.get('fabric') or 'fabric not set'}, {item.get('season') or 'season not set'}")


def render_feedback_history() -> None:
    st.markdown("## Feedback and wear history")
    user_id = get_current_user_id()

    outfit = st.session_state.get("selected_outfit")
    if outfit:
        st.markdown("### Rate selected outfit")
        rating = st.slider("Rating", 1, 5, 4)
        comment = st.text_area("Comment")
        if st.button("Submit rating", type="primary"):
            record_outfit_feedback(DATABASE_PATH, user_id, outfit["item_ids"], rating, comment)
            st.success("Feedback saved.")

    st.markdown("### Recent wear history")
    history = get_outfit_history(DATABASE_PATH, user_id)
    if not history:
        st.info("No outfits have been marked as worn yet.")
    else:
        for entry in history:
            st.write(f"- {entry['worn_at']} — {entry.get('item_names', 'Outfit')}")

    feedback = get_outfit_feedback(DATABASE_PATH, user_id)
    if feedback:
        st.markdown("### Previous ratings")
        for entry in feedback:
            st.write(f"- {'★' * entry['rating']}{'☆' * (5-entry['rating'])} — {entry['comment'] or 'No comment'}")
