from flask import Flask, render_template, request
import os
from flask_sqlalchemy  import SQLAlchemy
from sqlalchemy.ext.automap import automap_base
import sqlite3
import math
import re
import numpy as np
import nltk
from nltk.tokenize import regexp_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords 
from nltk.tokenize import regexp_tokenize
from nltk.stem import PorterStemmer
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
from sqlalchemy import create_engine
from nltk.corpus import wordnet
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
import pickle
# from mytvpy.models import base

# base.User.query.all()

# basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
db_uri = "sqlite:///C:/Users/Antonio franco/Documents/IR/project/paper.db"
engine = create_engine(db_uri)
modelText = pickle.load(open('C:/Users/Antonio franco/Documents/IR/project/modelText', 'rb'))
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///C:/Users/Antonio franco/Documents/IR/project/paper.db"
# app.config['SQLACHEMY_TRACK_MODIFICATION'] = False
# db = SQLAlchemy(app)
# connection = sqlite3.connect(r"C:\Users\Antonio franco\Documents\IR\project\paper.db")
# c = connection.cursor()
# # ####################################################################### 
# Base = automap_base()
# Base.prepare(db.engine, reflect = True)


lt = engine.execute("SELECT word FROM Tfidf").fetchall()
dict_ = {item:1 for t in lt for item in t}
def pos_tagger(nltk_tag):
    if nltk_tag.startswith('J'):
        return wordnet.ADJ
    elif nltk_tag.startswith('V'):
        return wordnet.VERB
    elif nltk_tag.startswith('N'):
        return wordnet.NOUN
    elif nltk_tag.startswith('R'):
        return wordnet.ADV
    else:          
        return None

def lemmatized_sentence(tokarray):
    Word_Lemmatizer = WordNetLemmatizer()
    pos_tagged = nltk.pos_tag(tokarray)
    wordnet_tagged = list(map(lambda x: (x[0], pos_tagger(x[1])), pos_tagged))
    lemmatized_sentence = []
    for word, tag in wordnet_tagged:
        if tag is None:
            # if there is no available tag, append the token as is
            lemmatized_sentence.append(word)
        else:        
            # else use the tag to lemmatize the token
            lemmatized_sentence.append(Word_Lemmatizer.lemmatize(word, tag))
    return lemmatized_sentence

def my_tonkenizer(s):

    stop_words = set(stopwords.words('english'))
    s = s.lower()
    token = regexp_tokenize(s, "[\w']+")
    # token = nltk.tokenize.word_tokenize(token)
    token = [w for w in token  if not w in stop_words]
    token = [t for t in token if len(t) >= 2]
    token = lemmatized_sentence(token)
    # token = [snow_stemmer.stem(t) for t in token]
    token = [w for w in token  if not w in stop_words]
    return token

def search(s):
    
    tokens = my_tonkenizer(s)

    res = np.zeros(2143, dtype=float)
    my_search = []
    found = False

    for tok in tokens :
        if tok in dict_:
            
            try:
                check_word = engine.execute("SELECT doc_value FROM Tfidf WHERE word = '"+str(tok)+"' ").fetchall()
                
                lts = re.findall(r"[-+]?\d*\.\d+|\d+", str(check_word))
                # results = list(map(int, lts))
                num = np.array(lts)
                
                num = num.astype(np.float)
                # lt
                res = [x + y for x, y in zip(res, num)]
                print(res)
                found = True
            except:
                continue
    if found:       
        ind = np.argmax(res)+1
        pa = engine.execute("SELECT paper.title, paper.authors, paper.date, paper.description, paper.title_link FROM paper WHERE docId = "+str(ind)+";").fetchall()
        new_d = [[title, authors, day, description, title_link] for title, authors, day, description, title_link in pa]
        my_search.append(new_d)
        lt = engine.execute("SELECT order_docs FROM cos_similarity WHERE wordId = "+str(ind)+";").fetchall()
        lt = re.findall(r"[-+]?\d*\.\d+|\d+", str(lt))
        nu = np.array(lt)
        nu = nu.astype(np.int32)
        for n in range(1, len(nu)):
            pa = engine.execute("SELECT paper.title, paper.authors, paper.date, paper.description, paper.title_link FROM paper WHERE docId = "+str(nu[n])+";").fetchall()
            new_d = [[title, authors, day, description, title_link] for title, authors, day, description, title_link in pa]
            my_search.append(new_d)
    return my_search


def pred(s):
    ar = []
    ar.append(s)
    return modelText.predict(ar)[0]


@app.route('/')
def index():
    my_search = []
    prediction = ""
    key = ""
    # pa = engine.execute("SELECT paper.title, paper.authors, paper.date, paper.description, paper.title_link FROM paper WHERE docId = "+str(5)+";").fetchall()
    # new_d = [[title, authors, day, description, title_link] for title, authors, day, description, title_link in pa]
    # my_search.append(new_d)
    # print(my_search[0][0][1])
    # print( new_d)
    if request.args.get('search'):
        key = request.args.get('search')
        if key.strip() != "":
            my_search = search(key.strip())
            prediction = pred(key.strip())
            key = key.strip() 
            # k =key.strip() 
    # print(search(key.strip()))
    
    
    return render_template('basic.html', my_search=my_search, prediction=prediction, key=key)

if __name__ == '__main__':
    app.run(debug=True)