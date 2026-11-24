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

## Milestone 6: Machine-learning outfit compatibility

Milestone 6 adds a Random Forest compatibility classifier to rank complete clothing combinations.

### Compatibility model

- Searches `data/raw/` for local Polyvore-style JSON, JSONL, or CSV metadata.
- If Polyvore metadata is unavailable, trains from a documented built-in sample dataset of positive and deliberately mismatched negative combinations.
- Extracts category distributions, mean pairwise colour distance, embedding similarity, category compatibility, and metadata agreement features.
- Reports accuracy, precision, recall, F1-score, and ROC-AUC.
- Saves the trained model and provenance/metrics to `models/compatibility_model.joblib` with Joblib.

The fallback model is not presented as a Polyvore-trained model. The saved artifact metadata identifies whether its training source was Polyvore or fallback sample data.

### Training and testing

```bash
python -c "from src.compatibility_model import train_model; print(train_model())"
pytest tests/test_compatibility_model.py tests/test_recommendation.py -q
pytest -q
streamlit run app.py
```

The recommendation page combines the existing rule-based score with the model probability and displays a compatibility percentage from 0% to 100%.

## Milestone 7: Real-time weather-aware recommendations

Milestone 7 integrates current weather from OpenWeather into outfit ranking.

### Obtain an OpenWeather API key

1. Create an account at https://home.openweathermap.org/users/sign_up.
2. Open https://home.openweathermap.org/api_keys.
3. Copy an API key or create a new named key.
4. Copy `.env.example` to `.env`.
5. Set `OPENWEATHER_API_KEY=your_api_key` in `.env`.

New OpenWeather keys can take several minutes to become active. Never commit `.env` or paste a real key into source code.

### Configure and run

Windows PowerShell:

```powershell
copy .env.example .env
$env:OPENWEATHER_API_KEY="your_api_key"
streamlit run app.py
```

Open **Recommendations**, select a city, and click **Fetch current weather**. If the API key is missing or unavailable, select **Manual weather fallback** and enter a temperature, condition, and rain state.

The recommendation engine considers temperature, season, rain, cold-weather categories, warm-weather categories, and item season/fabric metadata in its ranking. API/network failures do not stop the app; manual weather remains available.

### Test Milestone 7

```bash
pytest tests/test_weather.py tests/test_recommendation.py -q
streamlit run app.py
```

## Milestone 8: Integer linear programming outfit optimization

Milestone 8 uses PuLP and binary decision variables to choose the best complete outfits.

### Mathematical formulation

For each valid candidate outfit $c$, a binary variable $y_c$ is 1 when that outfit is selected and 0 otherwise.

$$
\max \sum_c y_c \left(S_c + W_c + O_c + P_c - R_c\right)
$$

- $S_c$: style compatibility from the existing rule and Milestone 6 model scores.
- $W_c$: weather suitability from the existing weather module.
- $O_c$: occasion suitability.
- $P_c$: match to categories, fabrics, and colours preferred by the user.
- $R_c$: repetition penalty for items in recent outfit history.

Hard constraints are built into candidate generation: every result must contain exactly one valid top-and-bottom or one dress, exactly one footwear item, and at most one optional outerwear item. Each optimization run also requires `sum(y) = 1`; previously selected candidates are forced to zero so the five returned outfits are different.

### Run and test

```bash
pip install -r requirements.txt
pytest tests/test_optimizer.py tests/test_database.py tests/test_recommendation.py tests/test_weather.py -q
streamlit run app.py
```

The Recommendations page provides occasion and preference controls and allows each suggestion to be marked as worn. Marked outfits are stored in SQLite and used to reduce the score of recently worn items.

## Current milestone status

- Milestone 1 complete: project structure, homepage, and app configuration.
- Milestone 2 complete: dataset cleaning and preparation utilities.
- Milestone 3 complete: image preprocessing and feature extraction.
- Milestone 4 complete: SQLite wardrobe CRUD and Streamlit wardrobe management.
- Milestone 5 complete: content-based outfit generation, compatibility scoring, ranking, and the recommendations page.
- Milestone 6 complete: machine-learning outfit compatibility model.
- Milestone 7 complete: real-time weather-aware outfit recommendations.
- Milestone 8 complete: PuLP integer-linear outfit optimization, preferences, and recent-wear penalty.

## Milestone 9: Complete application integration

Milestone 9 combines authentication, wardrobe management, weather and occasion selection, ML/rule-based recommendations, outfit details, ratings, and wear history in one Streamlit application.

### Integrated pages

- Home: wardrobe and activity summary
- Login and Registration: local SQLite accounts with salted PBKDF2 password hashes
- Upload Wardrobe: image processing and feature extraction
- My Wardrobe: uploaded images and item CRUD
- Weather and Occasion: OpenWeather or manual fallback plus preferences
- Outfit Recommendations: top five optimized outfits with compatibility and weather scores
- Outfit Details: item breakdown and recommendation explanation
- Feedback and Wear History: ratings, comments, and recently worn outfits

### Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

For OpenWeather, set `OPENWEATHER_API_KEY` in `.env`. Manual weather remains available when no key or internet connection is available.

### Testing

```bash
pytest -q
pytest tests/test_milestone9_integration.py tests/test_optimizer.py tests/test_database.py tests/test_recommendation.py tests/test_weather.py -q
```

### User workflow

1. Create or log in to an account.
2. Upload at least three compatible clothing items.
3. Open Weather and Occasion, select a city or enter manual weather, and choose an occasion.
4. Open Outfit Recommendations and generate the top five outfits.
5. Open an outfit for details, mark it as worn, or submit a rating.
6. Review ratings and wear history in Feedback and Wear History.

Recently worn item combinations are passed to the existing Milestone 8 optimizer as repetition penalties, so recently used combinations are ranked lower.

## Current milestone status

- Milestone 1 complete: project structure and app foundation.
- Milestone 2 complete: dataset loading and preprocessing utilities.
- Milestone 3 complete: image preprocessing and feature extraction.
- Milestone 4 complete: SQLite wardrobe management.
- Milestone 5 complete: content-based recommendations.
- Milestone 6 complete: outfit compatibility model integration.
- Milestone 7 complete: weather-aware recommendations.
- Milestone 8 complete: integer-linear outfit optimization.
- Milestone 9 complete: full Streamlit integration, authentication, feedback, details, and wear history.

# Milestone 10: Final submission and deployment

## Quick start

```powershell
cd C:\Users\Dc\Desktop\MLMP
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

Open `http://localhost:8501`.

## Environment configuration

Copy `.env.example` to `.env`. `OPENWEATHER_API_KEY` is optional because manual weather fallback is supported.

```dotenv
OPENWEATHER_API_KEY=your_openweather_api_key_here
APP_ENV=development
SECRET_KEY=change_this_secret_key
DATABASE_PATH=data/app.db
```

Never commit `.env`, API keys, passwords, database files, or personal uploads.

## Testing

```powershell
pytest -q
pytest tests/test_database.py tests/test_image_processing.py tests/test_recommendation.py tests/test_weather.py tests/test_optimizer.py -q
pytest tests/test_milestone9_integration.py tests/test_evaluation.py -q
```

## Evaluation

The project contains Precision@K, Recall@K, Average Precision, and MAP utilities in `src/evaluation.py`. The synthetic/fallback data only demonstrates the compatibility classifier; real recommendation quality requires user relevance labels or externally supplied outfits.

Generate the classifier metric chart:

```powershell
python -c "from src.compatibility_model import train_model; from src.evaluation_visualization import plot_classifier_metrics; r=train_model(); print(r['metrics']); print(plot_classifier_metrics(r['metrics']))"
```

The chart is saved to `assets/evaluation/model_metrics.png`. Do not present fallback model metrics as Polyvore validation.

## Streamlit Community Cloud

1. Push the repository to GitHub.
2. Create a Streamlit Community Cloud app using `app.py`.
3. Add secrets in Community Cloud:

```toml
OPENWEATHER_API_KEY = "replace_with_your_key"
APP_ENV = "production"
SECRET_KEY = "replace_with_a_long_random_secret"
DATABASE_PATH = "data/app.db"
```

SQLite and uploaded files are ephemeral on a free cloud process and may reset after redeployment or restart.

## Screenshots

Add final screenshots to `assets/screenshots/`:

- Home
- Wardrobe
- Weather and Occasion
- Recommendations
- Outfit Details
- Feedback and Wear History

## Limitations

- Authentication is local SQLite and is not an enterprise identity system.
- Community Cloud storage is ephemeral.
- Fallback compatibility model data is synthetic unless real Polyvore-style metadata is supplied.
- MAP/Precision/Recall require actual relevance labels.
- OpenWeather availability depends on network and API quota.

## Future improvements

- Add persistent cloud database and object storage.
- Add OAuth and stronger account security.
- Train from a real labeled outfit dataset.
- Learn preferences from ratings and wear history.
- Add CI, automated browser tests, and accessibility checks.
