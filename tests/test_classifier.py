"""TextClassification.ipynb logic: TF-IDF + LinearSVC pipeline on export.csv (committed, 474 rows)."""
import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parent.parent
LABELS = {"art", "business", "engineering", "health", "irrelevant"}


def test_export_csv_has_expected_shape_and_labels():
    df = pd.read_csv(ROOT / "export.csv")
    assert list(df.columns) == ["text", "class"]
    assert len(df) == 474
    assert set(df["class"]) == LABELS
    assert df["text"].notna().all()


def test_linear_svc_pipeline_matches_notebook_accuracy():
    """Same split as notebook cell 5 (test_size=0.3, random_state=42); the saved notebook output says 0.92."""
    df = pd.read_csv(ROOT / "export.csv")
    X_train, X_test, y_train, y_test = train_test_split(df["text"], df["class"], test_size=0.3, random_state=42)
    assert len(X_test) == 143
    model = Pipeline([("tfidf", TfidfVectorizer()), ("clf", LinearSVC())]).fit(X_train, y_train)
    accuracy = (model.predict(X_test) == y_test).mean()
    assert accuracy >= 0.88   # slack for scikit-learn version differences


def test_pickled_pipeline_predicts_from_raw_string(mini_corpus, tmp_path):
    """What flask_back/basic.py does: unpickle, call predict on a one-element list of raw text."""
    model = Pipeline([("tfidf", TfidfVectorizer()), ("clf", LinearSVC())]).fit(mini_corpus["text"], mini_corpus["class"])
    path = tmp_path / "modelText"
    path.write_bytes(pickle.dumps(model))
    loaded = pickle.loads(path.read_bytes())
    assert loaded.predict(["the museum opened an art exhibition"])[0] == "art"
