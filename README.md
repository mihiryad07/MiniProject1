# Personalized Clothing Recommendation System

A beginner-friendly personal wardrobe recommendation system built with Python, Streamlit, and SQLite.

## Project objective

This application helps users:
- upload clothing items
- store wardrobe data in a local SQLite database
- view clothing features and categories
- receive personalized recommendations
- use weather and occasion-based logic

This milestone is the initial project setup and app foundation.

## Project structure

```text
MLMP/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── app.py
├── src/
│   ├── __init__.py
│   ├── ui/
│   ├── auth/
│   ├── database/
│   ├── wardrobe/
│   ├── recommendation/
│   ├── weather/
│   └── utils/
├── data/
│   ├── raw/
│   └── processed/
├── models/
├── assets/
├── tests/
└── .venv/
```

## Technology stack

- Python 3.11
- Streamlit
- SQLite
- Pandas
- NumPy
- Python-dotenv
- Pytest

## Local setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create environment variables

Copy the example file:

```bash
copy .env.example .env
```

Then update the values in `.env` if needed.

### 4. Run the app

```bash
streamlit run app.py
```

## Git setup

### 1. Initialize Git

```bash
git init
```

### 2. Add remote repository

```bash
git remote add origin https://github.com/mihiryad07/MiniProject1.git
```

### 3. Check remote

```bash
git remote -v
```

### 4. Add files and commit

```bash
git add .
git commit -m "Initial project structure and Streamlit homepage"
```

### 5. Push to GitHub

```bash
git push -u origin main
```

If your branch is not `main`, replace it with your current branch name.

## Notes

- The project is intentionally kept lightweight for beginner use and Streamlit Community Cloud deployment.
- This is the initial milestone only; machine learning code will be added in later milestones.
- Do not commit API keys or personal secrets.

## Current milestone status

Milestone 1 complete: project structure, homepage, sidebar, app configuration, and initialization setup.
