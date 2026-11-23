import streamlit as st

from src.config import APP_NAME, APP_VERSION, PAGE_ICON, DATABASE_PATH
from src.database import (
    initialize_database,
    get_or_create_default_user,
    record_outfit_worn,
    get_recently_worn_item_ids,
)
from src.recommendation import generate_outfit_combinations
from src.weather import WeatherAPIError, fetch_current_weather, manual_weather, weather_clothing_advice
from src.wardrobe import (
    add_clothing_item,
    delete_clothing_item,
    list_clothing_items,
    update_clothing_item,
)
from src.ui.pages import (
    render_auth,
    render_feedback_history,
    render_home,
    render_outfit_details,
    render_recommendations,
    render_upload,
    render_wardrobe,
    render_weather_occasion,
)


st.set_page_config(page_title=APP_NAME, page_icon=PAGE_ICON, layout="wide", initial_sidebar_state="expanded")
initialize_database(DATABASE_PATH)

st.title(f"{PAGE_ICON} {APP_NAME}")
st.caption(f"Version {APP_VERSION} • Personalized clothing recommendations")
st.write(
    "Welcome to the Personalized Clothing Recommendation System. "
    "Manage your wardrobe and receive outfit suggestions based on occasion, weather, and personal style."
)
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Wardrobe")
    st.write("Upload and organize clothing items.")
with col2:
    st.subheader("Recommendations")
    st.write("Get optimized outfits for weather and occasion.")
with col3:
    st.subheader("Insights")
    st.write("Track clothing combinations and recent wear.")

st.sidebar.title("Navigation")
selected_page = st.sidebar.selectbox(
    "Go to",
    [
        "Home",
        "Login and Registration",
        "Upload Wardrobe",
        "My Wardrobe",
        "Weather and Occasion",
        "Outfit Recommendations",
        "Outfit Details",
        "Feedback and Wear History",
    ],
)
st.sidebar.markdown("---")
st.sidebar.caption("Project: Personalized Clothing Recommendation System")
st.sidebar.caption("Team: Noob Coders")

if selected_page == "Home":
    render_home()

elif selected_page == "Login and Registration":
    render_auth()

elif selected_page == "Upload Wardrobe":
    render_upload()

elif selected_page == "My Wardrobe":
    st.header("My Wardrobe")
    add_tab, view_tab, update_tab, delete_tab = st.tabs(
        ["Add clothing", "View wardrobe", "Update", "Delete"]
    )

    items = list_clothing_items(DATABASE_PATH)

    with add_tab:
        st.subheader("Add a clothing item")
        with st.form("add_clothing_form", clear_on_submit=True):
            uploaded_file = st.file_uploader("Upload clothing image", type=["png", "jpg", "jpeg", "webp"])
            name = st.text_input("Item name")
            category = st.selectbox(
                "Category",
                ["T-shirt", "Shirt", "Pants", "Jeans", "Dress", "Skirt", "Jacket", "Hoodie", "Sweater", "Shoes", "Accessory", "Other"],
            )
            fabric = st.selectbox("Fabric", ["Cotton", "Polyester", "Wool", "Silk", "Denim", "Linen", "Leather", "Other"])
            season = st.selectbox("Season", ["Summer", "Winter", "Spring", "Autumn", "All-season"])
            occasion = st.selectbox("Occasion", ["Casual", "Formal", "Party", "Sports", "Business", "Beach", "Other"])
            submitted = st.form_submit_button("Add to wardrobe")

        if submitted:
            if uploaded_file is None:
                st.error("Please upload a clothing image.")
            elif not name.strip():
                st.error("Please enter an item name.")
            else:
                try:
                    item = add_clothing_item(
                        uploaded_file,
                        name=name,
                        category=category,
                        fabric=fabric,
                        season=season,
                        occasion=occasion,
                        db_path=DATABASE_PATH,
                    )
                    st.success("Clothing item added successfully.")
                    st.image(item["image_path"], caption=f"{item['name']} — {item['dominant_color']}", use_container_width=True)
                except Exception as exc:
                    st.error(f"Could not add clothing item: {exc}")

    with view_tab:
        st.subheader("Your clothing items")
        if not items:
            st.info("No clothing items yet. Add one from the first tab.")
        else:
            columns = st.columns(3)
            for index, item in enumerate(items):
                with columns[index % 3]:
                    if item["image_path"]:
                        st.image(item["image_path"], use_container_width=True)
                    st.markdown(f"**{item['name']}**")
                    st.write(f"Category: {item['category']}")
                    st.write(f"Fabric: {item['fabric'] or 'Not set'}")
                    st.write(f"Season: {item['season'] or 'Not set'}")
                    st.write(f"Occasion: {item['occasion'] or 'Not set'}")
                    st.write(f"Dominant colour: {item['dominant_color'] or 'Not available'}")

    with update_tab:
        st.subheader("Update clothing information")
        if not items:
            st.info("No clothing items to update.")
        else:
            selected = st.selectbox("Choose an item", items, format_func=lambda item: f"{item['id']} — {item['name']}", key="update_item")
            with st.form("update_clothing_form"):
                name = st.text_input("Item name", value=selected["name"])
                category = st.text_input("Category", value=selected["category"])
                fabric = st.text_input("Fabric", value=selected["fabric"] or "")
                season = st.text_input("Season", value=selected["season"] or "")
                occasion = st.text_input("Occasion", value=selected["occasion"] or "")
                submitted = st.form_submit_button("Save changes")

            if submitted:
                updated = update_clothing_item(
                    selected["id"],
                    {"name": name.strip(), "category": category.strip(), "fabric": fabric.strip(), "season": season.strip(), "occasion": occasion.strip()},
                    DATABASE_PATH,
                )
                if updated:
                    st.success("Clothing item updated. Refresh the page to see changes.")
                else:
                    st.error("Clothing item could not be updated.")

    with delete_tab:
        st.subheader("Delete a clothing item")
        if not items:
            st.info("No clothing items to delete.")
        else:
            selected = st.selectbox("Choose an item to delete", items, format_func=lambda item: f"{item['id']} — {item['name']}", key="delete_item")
            if st.button("Delete selected item", type="primary"):
                if delete_clothing_item(selected["id"], DATABASE_PATH):
                    st.success("Clothing item deleted. Refresh the page to see changes.")
                else:
                    st.error("Clothing item could not be deleted.")

elif selected_page == "Weather and Occasion":
    render_weather_occasion()

elif selected_page == "Outfit Recommendations":
    st.header("Outfit Recommendations")
    wardrobe_items = list_clothing_items(DATABASE_PATH)

    if len(wardrobe_items) < 2:
        st.info("Add at least two clothing items to generate outfit combinations.")
    else:
        st.subheader("Current weather")
        weather_mode = st.radio("Weather source", ["OpenWeather API", "Manual weather fallback"], horizontal=True)
        current_weather = None

        if weather_mode == "OpenWeather API":
            city_choices = [
                "Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad",
                "Pune", "Ahmedabad", "London", "New York", "Dubai", "Singapore",
                "Tokyo", "Sydney", "Paris", "Other",
            ]
            selected_city = st.selectbox("Select a city", city_choices)
            city = st.text_input("Enter city name", value="Mumbai") if selected_city == "Other" else selected_city

            if st.button("Fetch current weather", type="primary"):
                st.session_state.pop("milestone7_weather", None)
                try:
                    current_weather = fetch_current_weather(city)
                    st.session_state["milestone7_weather"] = current_weather
                except WeatherAPIError as exc:
                    st.error(f"Weather unavailable: {exc}")
                    st.info("Use the Manual weather fallback below, or check that OPENWEATHER_API_KEY is configured.")

            current_weather = st.session_state.get("milestone7_weather") if current_weather is None else current_weather
        else:
            manual_temperature = st.number_input("Temperature (°C)", min_value=-50.0, max_value=60.0, value=20.0, step=1.0)
            manual_condition = st.selectbox("Weather condition", ["Clear", "Clouds", "Rain", "Drizzle", "Thunderstorm", "Snow", "Fog"])
            manual_rain = st.checkbox("Raining", value=manual_condition in {"Rain", "Drizzle", "Thunderstorm"})
            current_weather = manual_weather(manual_temperature, manual_condition, manual_rain)

        if current_weather:
            advice = weather_clothing_advice(current_weather)
            st.success(
                f"{current_weather['city']}: {current_weather['temperature_c']:.1f}°C, "
                f"{current_weather['description']} ({current_weather['source']})"
            )
            st.caption(f"Season: {advice['season']} — {advice['advice']}")

        occasion_filter = st.selectbox(
            "Occasion filter",
            ["Any", "Casual", "Formal", "Party", "Sports", "Business", "Beach"],
        )
        requested_occasion = None if occasion_filter == "Any" else occasion_filter

        st.subheader("User preferences")
        preference_categories = st.multiselect(
            "Preferred categories",
            sorted({str(item.get("category", "")).strip().lower() for item in wardrobe_items if item.get("category")}),
        )
        preference_fabrics = st.multiselect(
            "Preferred fabrics",
            sorted({str(item.get("fabric", "")).strip().lower() for item in wardrobe_items if item.get("fabric")}),
        )
        preference_colours = st.text_input("Preferred colours (comma-separated hex codes)", value="", help="Example: #111111, #FFFFFF")
        preferences = {
            "preferred_categories": preference_categories,
            "preferred_fabrics": preference_fabrics,
            "preferred_colours": [colour.strip().upper() for colour in preference_colours.split(",") if colour.strip()],
        }

        user_id = get_or_create_default_user(DATABASE_PATH)
        recently_worn_ids = get_recently_worn_item_ids(DATABASE_PATH, user_id, limit=10)
        recommendations = generate_outfit_combinations(
            wardrobe_items,
            occasion=requested_occasion,
            top_n=5,
            weather=current_weather,
            preferences=preferences,
            recently_worn_ids=recently_worn_ids,
        )

        if not recommendations:
            st.info("Not enough compatible categories yet. Try shirts with pants or jeans, or add a dress and shoes.")
        else:
            st.caption("Ranked by binary integer-linear optimization using style, weather, occasion, preferences, and repetition.")
            for rank, outfit in enumerate(recommendations, start=1):
                st.subheader(
                    f"{rank}. {outfit['reason']} — score {outfit['score']:.2f} "
                    f"— compatible {outfit.get('compatibility_probability', 0.5):.1%} "
                    f"— weather {outfit.get('weather_suitability', 0.5):.1%}"
                )
                columns = st.columns(len(outfit["items"]))
                for column, item in zip(columns, outfit["items"]):
                    with column:
                        if item.get("image_path"):
                            st.image(item["image_path"], use_container_width=True)
                        st.markdown(f"**{item['name']}**")
                        st.write(f"{item['category']} • {item['dominant_color'] or 'No colour'}")
                if st.button("Mark this outfit as worn", key=f"worn_{rank}_{'-'.join(map(str, outfit['item_ids']))}"):
                    record_outfit_worn(DATABASE_PATH, user_id, outfit["item_ids"])
                    st.success("Outfit recorded as recently worn.")

elif selected_page == "Outfit Details":
    render_outfit_details()

elif selected_page == "Feedback and Wear History":
    render_feedback_history()

elif selected_page == "Settings":
    st.info("Application settings will be configured later.")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: linear-gradient(145deg, #f7f9fc, #edf3f8); }
[data-testid="stSidebar"] { background: #172033; }
[data-testid="stSidebar"] * { color: #f7f9fc; }
[data-testid="stMetric"] { background: white; border-radius: 16px; padding: 16px; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg, #7259d9, #4d71d8); }
img { border-radius: 14px; }
.block-container { max-width: 1180px; padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("---")
st.write("Milestone 9: Complete integrated wardrobe recommendation application.")
