"""Shared fixtures. Nothing here touches the network or the real (uncommitted) paper.db / modelText."""
import os
import pickle
import sqlite3
import sys
from pathlib import Path

import nltk
import pandas as pd
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _ensure_nltk_data():
    """The tokenizer needs three NLTK corpora; download only if missing (CI has network, tests do not)."""
    needed = {
        "corpora/stopwords": "stopwords",
        "corpora/wordnet": "wordnet",
        "taggers/averaged_perceptron_tagger_eng": "averaged_perceptron_tagger_eng",
        "taggers/averaged_perceptron_tagger": "averaged_perceptron_tagger",
    }
    for path, name in needed.items():
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(name, quiet=True)


_ensure_nltk_data()


@pytest.fixture(scope="session")
def mini_corpus():
    return pd.read_csv(FIXTURES / "mini_corpus.csv")


@pytest.fixture(scope="session")
def search_env(tmp_path_factory):
    """A tiny paper.db and a tiny pickled model, wired in through the IR_DB_PATH / IR_MODEL_PATH variables."""
    tmp = tmp_path_factory.mktemp("ir_data")
    db = tmp / "paper.db"
    con = sqlite3.connect(db)
    con.executescript((FIXTURES / "search_fixture.sql").read_text())
    con.commit()
    con.close()

    corpus = pd.read_csv(FIXTURES / "mini_corpus.csv")
    model = Pipeline([("tfidf", TfidfVectorizer()), ("clf", LinearSVC())])
    model.fit(corpus["text"], corpus["class"])
    model_path = tmp / "modelText"
    with open(model_path, "wb") as fh:
        pickle.dump(model, fh)
    return {"db": str(db), "model": str(model_path)}


@pytest.fixture(scope="session")
def basic(search_env):
    """Import flask_back/basic.py against the fixtures (it loads the DB and model at import time)."""
    os.environ["IR_DB_PATH"] = search_env["db"]
    os.environ["IR_MODEL_PATH"] = search_env["model"]
    sys.path.insert(0, str(ROOT / "flask_back"))
    # basic.py calls nltk.download(...) at import; the data is already present, so make it a no-op.
    real_download = nltk.download
    nltk.download = lambda *a, **k: True
    try:
        import basic as module
    finally:
        nltk.download = real_download
    return module
