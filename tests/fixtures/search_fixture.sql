-- Three invented papers; weights are hand-made, not scraped data.
CREATE TABLE paper (docId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, title TEXT, authors TEXT, date TEXT,
    journal TEXT, pages TEXT, conference TEXT, publisher TEXT, description TEXT, title_link TEXT,
    name_p TEXT, link_p TEXT, description_p TEXT, areas_p TEXT);
INSERT INTO paper (title, authors, date, description, title_link) VALUES
    ('Neural ranking of documents', 'A Author', '2020', 'Ranking with neural networks', 'example.org/1'),
    ('Soil chemistry survey', 'B Author', '2019', 'Chemistry of soil samples', 'example.org/2'),
    ('Ranking evaluation metrics', 'C Author', '2021', 'Metrics for ranking evaluation', 'example.org/3');

-- word -> one TF-IDF weight per document (docId 1..3), stored as text like the real table
CREATE TABLE Tfidf (word TEXT, doc_value TEXT);
INSERT INTO Tfidf VALUES ('rank', '[0.9, 0.0, 0.4]'), ('soil', '[0.0, 0.8, 0.0]'), ('neural', '[0.7, 0.0, 0.0]'), ('document', '[0.5, 0.0, 0.3]'),
    ('o''brien', '[0.1, 0.0, 0.6]');

-- doc -> all docs ranked by cosine similarity (column is called wordId in the real table, but holds a docId)
CREATE TABLE cos_similarity (wordId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, order_docs TEXT);
INSERT INTO cos_similarity (order_docs) VALUES ('[1, 3, 2]'), ('[2, 1, 3]'), ('[3, 1, 2]');
