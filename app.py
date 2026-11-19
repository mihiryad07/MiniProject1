import streamlit as st

from src.config import APP_NAME, APP_VERSION, PAGE_ICON, DATABASE_PATH
from src.database import initialize_database
from src.recommendation import generate_outfit_combinations
from src.wardrobe import (
    add_clothing_item,
    delete_clothing_item,
    list_clothing_items,
    update_clothing_item,
)


st.set_page_config(
    page_title=APP_NAME,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_database(DATABASE_PATH)

st.title(f"{PAGE_ICON} {APP_NAME}")
st.caption(f"Version {APP_VERSION} • Personalized clothing recommendations")

st.write(
    "Welcome to the Personalized Clothing Recommendation System. "
    "This application helps users manage their wardrobe and receive outfit suggestions based on occasion, weather, and personal style."
)

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Wardrobe")
    st.write("Upload and organize clothing items from your personal wardrobe.")

with col2:
    st.subheader("Recommendations")
    st.write("Get outfit suggestions based on occasion, weather, and user preferences.")

with col3:
    st.subheader("Insights")
    st.write("Track clothing combinations and improve outfit decisions over time.")

st.sidebar.title("Navigation")
selected_page = st.sidebar.selectbox(
    "Go to",
    ["Home", "Login", "Register", "Wardrobe", "Recommendations", "Settings"],
)

st.sidebar.markdown("---")
st.sidebar.caption("Project: Personalized Clothing Recommendation System")
st.sidebar.caption("Team: Noob Coders")

if selected_page == "Home":
    st.info("You are on the homepage.")
elif selected_page == "Login":
    st.info("Login page will be implemented in a future milestone.")
elif selected_page == "Register":
    st.info("Registration page will be implemented in a future milestone.")
elif selected_page == "Wardrobe":
    st.header("My Wardrobe")
    add_tab, view_tab, update_tab, delete_tab = st.tabs(
        ["Add clothing", "View wardrobe", "Update", "Delete"]
    )

    with add_tab:
        st.subheader("Add a clothing item")
        with st.form("add_clothing_form", clear_on_submit=True):
            uploaded_file = st.file_uploader(
                "Upload clothing image",
                type=["png", "jpg", "jpeg", "webp"],
            )
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

    items = list_clothing_items(DATABASE_PATH)

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
            selected = st.selectbox(
                "Choose an item",
                items,
                format_func=lambda item: f"{item['id']} — {item['name']}",
                key="update_item",
            )
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
                    {
                        "name": name.strip(),
                        "category": category.strip(),
                        "fabric": fabric.strip(),
                        "season": season.strip(),
                        "occasion": occasion.strip(),
                    },
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
            selected = st.selectbox(
                "Choose an item to delete",
                items,
                format_func=lambda item: f"{item['id']} — {item['name']}",
                key="delete_item",
            )
            if st.button("Delete selected item", type="primary"):
                if delete_clothing_item(selected["id"], DATABASE_PATH):
                    st.success("Clothing item deleted. Refresh the page to see changes.")
                else:
                    st.error("Clothing item could not be deleted.")

elif selected_page == "Recommendations":
    st.header("Outfit Recommendations")
    wardrobe_items = list_clothing_items(DATABASE_PATH)

    if len(wardrobe_items) < 2:
        st.info("Add at least two clothing items to generate outfit combinations.")
    else:
        occasion_filter = st.selectbox(
            "Occasion filter",
            ["Any", "Casual", "Formal", "Party", "Sports", "Business", "Beach"],
        )
        requested_occasion = None if occasion_filter == "Any" else occasion_filter

        recommendations = generate_outfit_combinations(
            wardrobe_items,
            occasion=requested_occasion,
            top_n=5,
        )

        if not recommendations:
            st.info("Not enough compatible categories yet. Try shirts with pants or jeans, or add a dress and shoes.")
        else:
            st.caption(
                "Ranked using cosine similarity for image embeddings, hex-colour compatibility, "
                "and category compatibility rules."
            )
            for rank, outfit in enumerate(recommendations, start=1):
                st.subheader(f"{rank}. {outfit['reason']} — score {outfit['score']:.2f}")
                columns = st.columns(len(outfit["items"]))
                for column, item in zip(columns, outfit["items"]):
                    with column:
                        if item.get("image_path"):
                            st.image(item["image_path"], use_container_width=True)
                        st.markdown(f"**{item['name']}**")
                        st.write(f"{item['category']} • {item['dominant_color'] or 'No colour'}")

elif selected_page == "Settings":
    st.info("Application settings will be configured later.")

st.markdown("---")
st.write("Milestone 5: Content-based outfit recommendations are ready.")
