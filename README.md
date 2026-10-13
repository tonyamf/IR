# IR

University information-retrieval project (2021, per the commit history): a small search engine over the
publications of researchers listed on one Google Scholar organisation page, plus a text classifier that
labels a query as one of five topics.

## What is in the repo

| File | What it is | Runs today? |
|---|---|---|
| `TextClassification.ipynb` | Trains a TF-IDF + Naive Bayes (Bayesian-optimised `alpha`) and a TF-IDF + LinearSVC classifier on `export.csv` (news-style texts, 5 classes) and pickles the SVC pipeline to `modelText`. | **Yes** |
| `export.csv` | Training data: columns `text`, `class` (art, business, engineering, health, irrelevant; 474 rows). | – |
| `flask_back/basic.py` | Flask search page: tokenises a query, scores documents from a `Tfidf` table, lists similar documents from a `cos_similarity` table and shows the predicted topic from `modelText`. | Starts, but needs data that is **not in the repo** (see below) |
| `spi.py` | Selenium scraper for Google Scholar that fills an SQLite `paper` table and an `inverted_index` table. | **No** (see below) |
| `BotG.ipynb`, `Untitled5.ipynb`, `Untitled6.ipynb` | Google Colab notebooks: Selenium/BeautifulSoup/Scrapy scraping experiments and cosine-similarity computation. They expect Google Drive files and a live Google Scholar. | **No** |

## How to run

Python 3.11 was used.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m ipykernel install --user --name python3
jupyter nbconvert --to notebook --execute --ExecutePreprocessor.kernel_name=python3 \
    TextClassification.ipynb --output executed.ipynb
```

This runs from the repo folder, reads `export.csv` and writes `modelText` (git-ignored). With the pinned
versions the printed classification reports match the outputs saved in the notebook: accuracy 0.88 for
Naive Bayes and 0.92 for LinearSVC on the 143-row test split (`random_state=42`).

### Flask page

```bash
cd flask_back
IR_DB_PATH=/path/to/paper.db IR_MODEL_PATH=/path/to/modelText python basic.py
```

`paper.db` (tables `paper`, `Tfidf`, `cos_similarity`) was produced by the scraper and the cosine-similarity
notebook and was never committed, so search results **cannot be reproduced** from this repo. The page needs
the NLTK data `stopwords`, `wordnet` and `averaged_perceptron_tagger` (the script tries to download them).
Only the empty-query page and the topic prediction were smoke-tested, against a dummy empty database.
Search itself is untested.

### Scraper and Colab notebooks

`spi.py` and the notebooks drive Google Scholar with Selenium 3 era calls (`find_element_by_xpath`,
`executable_path=`), Windows paths and CSS ids that Google may have changed. They were not run: they need a
browser driver, would hit Google Scholar repeatedly, and the Google Drive inputs are missing. Treat them as
reference code.

## Known limitations

- The numbers above come from a 474-row dataset and a single split; they say nothing about the quality of
  the paper search.
- `flask_back/basic.py` builds SQL by string concatenation and needs SQLAlchemy 1.4 (`engine.execute`).
- The scoring vector length (2143 documents) is hard-coded.
