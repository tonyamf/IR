"""Logic that lives inside notebooks / scripts that cannot simply be imported.

The code under test is read out of the project files (Untitled5.ipynb cells, spi.py functions) and executed, so
the tests exercise the author's real code, not a copy. spi.py is never imported as a module: doing so would start
Selenium and open Chrome.
"""
import ast
import json
import math
import re
import sqlite3
from pathlib import Path

import numpy as np
import pytest
from nltk.tokenize import regexp_tokenize

ROOT = Path(__file__).resolve().parent.parent


def _notebook_cell(name, index):
    nb = json.loads((ROOT / name).read_text(encoding="utf-8"))
    return "".join(nb["cells"][index]["source"])


@pytest.fixture(scope="module")
def cosine():
    src = _notebook_cell("Untitled5.ipynb", 5)
    # run as plain Python: no numba needed
    src = src.replace("from numba import jit", "").replace("@jit(nopython=True, parallel=True)", "")
    ns = {"np": np}
    exec(src, ns)
    return ns["cosine_similarity_numba"]


def test_cosine_identical_vectors_is_one(cosine):
    v = np.array([1.0, 2.0, 3.0])
    assert cosine(v, v) == pytest.approx(1.0)


def test_cosine_orthogonal_vectors_is_zero(cosine):
    assert cosine(np.array([1.0, 0.0]), np.array([0.0, 5.0])) == pytest.approx(0.0)


def test_cosine_ignores_vector_length(cosine):
    u = np.array([1.0, 1.0, 0.0])
    assert cosine(u, 10 * u) == pytest.approx(1.0)


@pytest.mark.xfail(strict=True, reason=(
    "Bug (2_fix/review.md B2): the function starts with cos_theta = 1 and only overwrites it when both vectors are "
    "non-zero, so a document with no TF-IDF weights is reported as identical to every other document."))
def test_cosine_with_zero_vector_is_zero(cosine):
    assert cosine(np.zeros(3), np.array([1.0, 2.0, 3.0])) == pytest.approx(0.0)


def test_tfidf_cell_builds_one_weight_per_document():
    """Untitled5.ipynb cell 6: posting list text -> per-document TF-IDF list (weight = count * log10(N/df))."""
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE inverted_index (wordId INTEGER PRIMARY KEY, word TEXT, doc_frequence TEXT)")
    con.execute("CREATE TABLE paper (docId INTEGER PRIMARY KEY, title TEXT)")
    con.executemany("INSERT INTO paper (title) VALUES (?)", [("a",), ("b",), ("c",), ("d",)])
    con.executemany("INSERT INTO inverted_index (word, doc_frequence) VALUES (?, ?)", [
        ("rare", "[2, 3]"),               # only doc 2, three times
        ("common", "[1, 1] [3, 2]"),      # docs 1 and 3
    ])
    ns = {"connection": con, "regexp_tokenize": regexp_tokenize, "math": math}
    src = _notebook_cell("Untitled5.ipynb", 6)
    exec(src, ns)
    dic = ns["dic_"]
    assert dic["rare"] == pytest.approx([0, 3 * math.log10(4 / 1), 0, 0])
    assert dic["common"] == pytest.approx([1 * math.log10(4 / 2), 0, 2 * math.log10(4 / 2), 0])


def _load_spi_functions(names):
    """Compile only the named top-level functions of spi.py (the rest of the file drives Chrome)."""
    tree = ast.parse((ROOT / "spi.py").read_text(encoding="utf-8"))
    wanted = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    module = ast.Module(body=wanted, type_ignores=[])
    import nltk
    from nltk.corpus import stopwords, wordnet
    from nltk.stem import WordNetLemmatizer
    ns = {"nltk": nltk, "stopwords": stopwords, "wordnet": wordnet, "WordNetLemmatizer": WordNetLemmatizer,
          "regexp_tokenize": regexp_tokenize, "sqlite3": sqlite3}
    exec(compile(module, "spi.py", "exec"), ns)
    return ns


@pytest.fixture()
def indexer(tmp_path, monkeypatch):
    """process_item writes to ./research2.db, so run it inside a temporary folder with the two tables."""
    monkeypatch.chdir(tmp_path)
    ns = _load_spi_functions({"pos_tagger", "lemmatized_sentence", "my_tonkenizer", "process_item"})
    con = sqlite3.connect("research2.db")
    con.execute('CREATE TABLE "paper"( docId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, title TEXT, authors TEXT, '
                'date TEXT, journal TEXT, pages TEXT, conference TEXT, publisher TEXT, description TEXT, '
                'title_link TEXT, name_p TEXT, link_p TEXT, description_p TEXT, areas_p TEXT)')
    con.execute('CREATE TABLE "inverted_index"(wordId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, word TEXT, '
                'doc_frequence TEXT)')
    con.commit()
    con.close()

    def add(title, description="", authors="", name_p=""):
        ns["process_item"](title, authors, "2020", "", "", "", "", description, "scholar.example/x",
                           name_p, "scholar.example/p", "", "")

    def postings(word):
        con = sqlite3.connect("research2.db")
        row = con.execute("SELECT doc_frequence FROM inverted_index WHERE word = ?", (word,)).fetchone()
        con.close()
        return None if row is None else row[0]

    return add, postings


def test_process_item_creates_postings_with_counts(indexer):
    add, postings = indexer
    add("Ranking ranking papers")
    assert postings("rank") == "[1, 2]"          # "Ranking ranking" -> lemma "rank", doc 1, twice
    assert postings("paper") == "[1, 1]"         # lemmatised plural -> "paper"


def test_process_item_appends_postings_for_a_second_document(indexer):
    add, postings = indexer
    add("Ranking methods")
    add("Ranking evaluation")
    assert postings("rank") == "[1, 1] [2, 1]"
    assert postings("evaluation") == "[2, 1]"


def test_process_item_does_not_index_urls(indexer):
    add, postings = indexer
    add("Soil")                                   # title_link is 'scholar.example/x'
    assert postings("scholar") is None


@pytest.mark.xfail(strict=True, reason=(
    "Bug (2_fix/review.md B3): the UPDATE for an existing word is built with string concatenation, so a token with "
    "an apostrophe makes the SQL invalid and the posting for the second document is silently dropped."))
def test_process_item_keeps_postings_of_words_with_apostrophes(indexer):
    add, postings = indexer
    add("O'Brien lecture")
    add("O'Brien interview")
    assert postings("o'brien") == "[1, 1] [2, 1]"
