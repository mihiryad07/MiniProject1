import streamlit as st

from src.config import APP_NAME, APP_VERSION, PAGE_ICON


st.set_page_config(
    page_title=APP_NAME,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title(f"{PAGE_ICON} {APP_NAME}")
st.caption(f"Version {APP_VERSION} • Personalized clothing recommendations")

st.write(
    "Welcome to the Personalized Clothing Recommendation System. "
    "This application will help users manage their wardrobe and receive outfit suggestions based on occasion, weather, and personal style."
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
st.sidebar.write("Select a section below:")

nav_options = [
    "Home",
    "Login",
    "Register",
    "Wardrobe",
    "Recommendations",
    "Settings",
]

selected_page = st.sidebar.selectbox("Go to", nav_options)

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
    st.info("Wardrobe management will be implemented in a future milestone.")
elif selected_page == "Recommendations":
    st.info("Recommendation system will be implemented in a future milestone.")
elif selected_page == "Settings":
    st.info("Application settings will be configured later.")

st.markdown("---")
st.write("Initial app setup complete. The project is ready for milestone-based development.")
