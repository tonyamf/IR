"""flask_back/basic.py: query tokenizer, search(), pred() and the / route, against the tiny fixture database."""
import pytest


def test_tokenizer_lowercases_removes_stopwords_and_lemmatises(basic):
    # "the"/"of" are stop words; "studies" -> "study" (noun), "running" -> "run" (verb)
    assert basic.my_tonkenizer("The studies of Running") == ["study", "run"]


def test_tokenizer_drops_single_letters(basic):
    assert basic.my_tonkenizer("a b soil") == ["soil"]


@pytest.mark.parametrize("tag,expected", [("JJ", "a"), ("VBD", "v"), ("NNS", "n"), ("RB", "r"), ("DT", None)])
def test_pos_tagger_maps_penn_tags_to_wordnet(basic, tag, expected):
    assert basic.pos_tagger(tag) == expected


def test_search_returns_best_document_first_then_neighbours(basic):
    # the query word is lemmatised to 'rank'; its weights are [0.9, 0.0, 0.4] -> doc 1 wins; cos_similarity for doc 1 is [1, 3, 2]
    results = basic.search("ranking")
    titles = [r[0][0] for r in results]
    assert titles == ["Neural ranking of documents", "Ranking evaluation metrics", "Soil chemistry survey"]


def test_search_sums_weights_of_several_query_words(basic):
    # soil [0, .8, 0] + neural [.7, 0, 0] + document [.5, 0, .3] -> doc 1 scores 1.2, doc 2 only 0.8
    assert basic.search("neural document soil")[0][0][0] == "Neural ranking of documents"
    # soil alone points at doc 2
    assert basic.search("soil")[0][0][0] == "Soil chemistry survey"


def test_search_unknown_words_gives_no_results(basic):
    assert basic.search("zzzunknownword") == []


def test_pred_returns_a_known_label(basic):
    assert basic.pred("hospital vaccine for patients") == "health"


def test_index_route(basic):
    client = basic.app.test_client()
    assert client.get("/").status_code == 200
    resp = client.get("/?search=soil")
    assert resp.status_code == 200
    assert b"Soil chemistry survey" in resp.data


@pytest.mark.xfail(strict=True, reason=(
    "Bug (2_fix/review.md B3): the word is looked up with string-built SQL, so a token containing an apostrophe "
    "raises a syntax error that the bare `except: continue` swallows; the word is silently ignored."))
def test_search_word_with_apostrophe_is_found(basic):
    # "o'brien" is in the vocabulary (weights [0.1, 0, 0.6] -> doc 3) and the tokenizer keeps the apostrophe
    results = basic.search("o'brien")
    assert results and results[0][0][0] == "Ranking evaluation metrics"


@pytest.mark.xfail(strict=True, reason=(
    "Bug (2_fix/review.md B4): lemmatisation depends on the part of speech guessed from context, so the same word "
    "is indexed as 'rank' in one phrase and 'ranking' in another. A query can then miss documents that contain the word."))
def test_same_word_gets_the_same_lemma_in_any_phrase(basic):
    assert basic.my_tonkenizer("ranking") == basic.my_tonkenizer("neural ranking")[1:]
