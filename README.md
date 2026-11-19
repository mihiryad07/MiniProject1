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
Milestone 2 complete: dataset loading, cleaning, normalization, and train/test preparation utilities.
Milestone 3 complete: image preprocessing and clothing feature extraction for recommendation pipeline support.

## Milestone 4: SQLite wardrobe management

Milestone 4 adds persistent wardrobe storage and a Streamlit wardrobe page.

### Database

The SQLite database is stored at `data/app.db` by default. The database contains:

- `users`: local user accounts
- `wardrobe_items`: clothing names, categories, image paths, dominant colours, fabric, season and occasion

The database is created automatically when the app starts or a wardrobe function is used.

### Wardrobe features

Open the app and choose **Wardrobe** in the sidebar:

1. Use **Add clothing** to upload an image and enter item details.
2. Use **View wardrobe** to display uploaded clothes and stored metadata.
3. Use **Update** to edit item information.
4. Use **Delete** to remove a clothing item.

The image processing module saves the uploaded image, and the feature extraction module stores its dominant colour as a hexadecimal value such as `#336699`.

### Test the database

Run all tests:

```bash
pytest -q
```

Run the wardrobe database test only:

```bash
pytest tests/test_database.py -q
```

Run the app:

```bash
streamlit run app.py
```

### Database reset

To start with a fresh wardrobe database, stop the app and delete `data/app.db`. The database and tables are recreated the next time the application starts.

## Current milestone status

- Milestone 1 complete: project structure, homepage, sidebar, app configuration, and initialization setup.
- Milestone 2 complete: dataset loading, cleaning, normalization, and train/test preparation utilities.
- Milestone 3 complete: image preprocessing and clothing feature extraction.
- Milestone 4 complete: SQLite wardrobe database, CRUD operations, image-to-database integration, and Streamlit wardrobe page.

## Milestone 5: Content-based outfit recommendations

Milestone 5 generates outfit combinations from the clothing items stored in SQLite.

### Recommendation process

1. Clothing embeddings and texture features are stored when an image is uploaded.
2. Cosine similarity compares image embeddings between wardrobe items.
3. Dominant hex colours receive a compatibility score.
4. Category rules determine whether tops, bottoms, shoes, or complete outfits fit together.
5. Each possible outfit is scored and ranked, then the top five are returned.

No trained machine-learning model is used. This is a beginner-friendly content-based ranking system that combines extracted image features and rule-based clothing compatibility.

### Test recommendations

```bash
pytest tests/test_recommendation.py -q
pytest -q
streamlit run app.py
```

Choose **Recommendations** in the sidebar after adding at least two wardrobe items.

## Current milestone status

- Milestone 1 complete: project structure, homepage, and app configuration.
- Milestone 2 complete: dataset cleaning and preparation utilities.
- Milestone 3 complete: image preprocessing and feature extraction.
- Milestone 4 complete: SQLite wardrobe CRUD and Streamlit wardrobe management.
- Milestone 5 complete: content-based outfit generation, compatibility scoring, ranking, and the recommendations page.
