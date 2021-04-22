import re
import nltk
import sqlite3
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords 
from nltk.tokenize import regexp_tokenize
from nltk.stem import PorterStemmer
from nltk.stem.snowball import SnowballStemmer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import time
import csv
from csv import writer
from bs4 import BeautifulSoup
import requests
import csv
from nltk.corpus import wordnet



url = 'https://scholar.google.co.uk/citations?view_op=view_org&hl=en&org=9117984065169182779'#'https://scholar.google.co.uk/citations?view_op=view_org&hl=en&org=9117984065169182779&after_author=XrAUAf3___8J&astart=690'#'
# I should put sleep somewhere
allowed_domains = 'scholar.google.co.uk'
options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_argument("disable-infobars")
options.add_argument("--disable-extensions")
driver = webdriver.Chrome(chrome_options=options, executable_path='C:/Users/Antonio franco/chromedriver_win32/chromedriver.exe')
driver.get(url)
allowed_domains = 'scholar.google.co.uk'

snow_stemmer = SnowballStemmer(language='english')
mypaper = {}
duplicate = {}
with open('C:/Users/Antonio franco/Documents/IR/project/duplicate.csv', mode='r', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    duplicate = {rows[0]:1 for rows in reader}
with open('C:/Users/Antonio franco/Documents/IR/project/papertemporary.csv', mode='r', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    mypaper = {rows[0]:1  for rows in reader}
connection = sqlite3.connect("research2.db")
c = connection.cursor()

c.execute(''' CREATE TABLE IF NOT EXISTS "paper"( docId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, title TEXT, authors TEXT, date TEXT, journal TEXT, pages TEXT, conference TEXT,
        publisher TEXT, description TEXT, title_link TEXT, name_p TEXT, link_p TEXT, description_p TEXT, areas_p TEXT); ''')
c.execute('''
    CREATE TABLE IF NOT EXISTS "inverted_index"(
        wordId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        word TEXT,
        doc_frequence TEXT
    );     
''')
connection.commit()
connection.commit()
connection.close()

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

def process_item(title,authors,date,journal,pages,conference,publisher,description,title_link, name_p, link_p, description_p,  areas_p):
    connection = sqlite3.connect("research2.db")
    c = connection.cursor()
    c.execute('''
        INSERT INTO paper('title', 'authors', 'date', 'journal', 'pages', 
        'conference', 'publisher', 'description', 'title_link', 
        'name_p', 'link_p', 'description_p', 'areas_p') VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''',(title,authors,date,journal,pages,conference,publisher,description,title_link,name_p,link_p,description_p,areas_p)
    )
    connection.commit()
    last_row = connection.execute('SELECT * FROM paper;').fetchall()[-1]
    word_index = {}
    for i in range(1, len(last_row)):
        if i == 9 or i == 11:
            continue
        tokens = my_tonkenizer(last_row[i])
        for tok in tokens:
            if tok in word_index:
                word_index[tok][1] = word_index[tok][1] + 1
            else:
                word_index[tok] = [last_row[0], 1]
    for wd in word_index:
        lt = connection.execute("SELECT word FROM inverted_index").fetchall()
        dict_ = {item:1 for t in lt for item in t}
        # dict_ = {l:1 for l in connection.execute("SELECT word FROM inverted_index").fetchall()}
        # print(dict_, lt)
        if wd in dict_:
            try:
                check_word = connection.execute("SELECT * FROM inverted_index WHERE word = '"+str(wd)+"' ").fetchall()[0]
                l = check_word[2] +" "+ str(word_index[wd])
                sql = "UPDATE inverted_index SET doc_frequence = '"+str(l)+"' WHERE word = '"+str(wd)+"';"
                c.execute(sql)
                connection.commit()
            except:
                continue
        else:
            sql = "INSERT INTO inverted_index ( word, doc_frequence ) VALUES (?, ?);"
            val = (wd, str(word_index[wd]))
            c.execute(sql, val)
            connection.commit()
    connection.close()


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

# options = webdriver.ChromeOptions()
# options.add_argument("start-maximized")
# options.add_argument("disable-infobars")
# options.add_argument("--disable-extensions")
# driver = webdriver.Chrome('chromedriver',chrome_options=options)
# driver.get(url)
df = {'title': [], 'authors': [], 'date': [],'journal': [], 'pages':[], 'conference': [],'publisher': [], 'description': [], 'num_citations': [], 'pdf_link': [], 'title_link': []}
d = {'title': "", 'authors': "", 'date': "",'journal': "", 'pages':"", 'conference': "",'publisher': "", 'description': "", 'num_citations': "", 'pdf_link': "", 'title_link': ""}
dfs = pd.DataFrame( columns=d, index=None)
#dfs = dfs.append(df, ignore_index=True)
#dfs.to_csv(r'C:/Users/Antonio franco/Documents/IR/cral.csv', index_label=False, index=False)

previous = ""
while True:
    try:
        # elemts = driver.find_element_by_xpath('//*[@id="gsc_authors_bottom_pag"]/div/span').text
        # Strings = elemts.split(" ")
        # # st = Strings[0]
        # # num = int(st)
        # if int(Strings[0) == int(Strings[2):
        #     break
        if previous == driver.find_element_by_xpath('//*[@id="gsc_authors_bottom_pag"]/div/span').text:

            break
        previous = driver.find_element_by_xpath('//*[@id="gsc_authors_bottom_pag"]/div/span').text
        element = driver.find_elements_by_xpath('//*[@id="gsc_sa_ccl"]/div/div/div/h3/a')
        #print(len(element))
        for ij in range(0, len(element)):
            print('prof')
            print(ij)
            elem = driver.find_elements_by_xpath('//*[@id="gsc_sa_ccl"]/div/div/div/h3/a')[ij]
            link = elem.get_attribute('href')
            elem.click()
            name_p = driver.find_element_by_xpath('//*[@id="gsc_prf_in"]').text 
            description_p = driver.find_element_by_xpath('//*[@id="gsc_prf_i"]/div[2]').text
            areas = driver.find_elements_by_xpath('//*[@id="gsc_prf_int"]/a')
            areas_p = []
            for area in areas:
               areas_p.append(area.text)
            if not areas_p:
                areas_p = ""
            areas_p = str(areas_p)[1:-1].replace("'", '')
            areas_p = str(areas_p).replace(",", '')
            link_p = driver.current_url
            thing =""
            while True:
                try:
                    if driver.find_element_by_xpath('//*[@id="gsc_a_nn"]').text != thing:
                        thing = driver.find_element_by_xpath('//*[@id="gsc_a_nn"]').text
                        driver.find_element_by_xpath('//*[@id="gsc_bpf_more"]/span/span[2]').click()  
                        time.sleep(0.5)                                      
                    else:
                        break
                except (TimeoutException, WebDriverException) as e:
                    print ("erro page ajax")
                    break

            num_articles = driver.find_elements_by_xpath('//*[@id="gsc_a_b"]/tr/td[1]/a')
            print(len(num_articles))  
            
            for i in range(0, len(num_articles)):
                print(i)
                paper = driver.find_elements_by_xpath('//*[@id="gsc_a_b"]/tr/td[1]/a')[i]
                title_link = allowed_domains + paper.get_attribute('data-href')
                title = paper.text
                aut = driver.find_elements_by_xpath('//*[@id="gsc_a_b"]/tr/td[1]/div[1]')[i]
                authors_layer = aut.text
                doc = {}
                doc_ = {}
                s = title.strip() + " " + authors_layer.strip()
                s = s.lower()
                token = regexp_tokenize(authors_layer.lower(), "[\w']+")
                tokdoc = {t:1 for t in token}
                tkp = regexp_tokenize(name_p.lower(), "[\w']+")
    
                for tk in tkp:
                    if tk in tokdoc:
                        
                        if s in duplicate:
                            break
                        duplicate[s] = 1
                        doc[s] =1
                        with open('C:/Users/Antonio franco/Documents/IR/project/duplicate.csv', 'a+', newline='', encoding='utf-8') as write_obj:
                            csv_writer = writer(write_obj)
                            csv_writer.writerow(doc)
                        if paper.get_attribute('data-href') in mypaper:
                            break
                        doc_[paper.get_attribute('data-href')] =1
                        mypaper[paper.get_attribute('data-href')] = 1
                        with open('C:/Users/Antonio franco/Documents/IR/project/papertemporary.csv', 'a+', newline='', encoding='utf-8') as write_obj:
                            csv_writer = writer(write_obj)
                            csv_writer.writerow(doc_)
                        
                        authors=""
                        date=""
                        journal=""
                        pages=""
                        conference=""
                        publisher=""
                        description=""
                        paper.click()
                        time.sleep(1)
                        body = driver.find_elements_by_xpath('//*[@id="gsc_vcd_table"]/div/div[1]')
                        for ii in range(1, len(body)+1):
                            if driver.find_element_by_xpath('//*[@id="gsc_vcd_table"]/div['+str(ii)+']/div[1]').text == 'Authors':
                                authors = driver.find_element_by_xpath('//*[@id="gsc_vcd_table"]/div['+str(ii)+']/div[2]').text
                            elif driver.find_element_by_xpath('//*[@id="gsc_vcd_table"]/div['+str(ii)+']/div[1]').text == 'Publication date':
                                date = driver.find_element_by_xpath('//*[@id="gsc_vcd_table"]/div['+str(ii)+']/div[2]').text

                            elif driver.find_element_by_xpath('//*[@id="gsc_vcd_table"]/div['+str(ii)+']/div[1]').text == 'Journal':
                                journal = driver.find_element_by_xpath('//*[@id="gsc_vcd_table"]/div['+str(ii)+']/div[2]').text

                            elif driver.find_element_by_xpath('//*[@id="gsc_vcd_table"]/div['+str(ii)+']/div[1]').text == 'Publisher':
                                publisher = driver.find_element_by_xpath('//*[@id="gsc_vcd_table"]/div['+str(ii)+']/div[2]').text

                            elif driver.find_element_by_xpath('//*[@id="gsc_vcd_table"]/div['+str(ii)+']/div[1]').text == 'Description':
                                description = driver.find_element_by_xpath('//*[@id="gsc_vcd_table"]/div['+str(ii)+']/div[2]').text

                            elif driver.find_element_by_xpath('//*[@id="gsc_vcd_table"]/div['+str(ii)+']/div[1]').text == 'Pages':
                                pages = driver.find_element_by_xpath('//*[@id="gsc_vcd_table"]/div['+str(ii)+']/div[2]').text

                            elif driver.find_element_by_xpath('//*[@id="gsc_vcd_table"]/div['+str(ii)+']/div[1]').text == 'Conference':
                                conference = driver.find_element_by_xpath('//*[@id="gsc_vcd_table"]/div['+str(ii)+']/div[2]').text 

                        print('------------ ++++++++++++--------------------------')
                        process_item(title,authors,date,journal,pages,conference,publisher,description,title_link, name_p, link_p, description_p,  areas_p)
                        print('--------------------------------------')
            
                # Append a list as new line to an old csv file
                # append_list_as_row('C:/Users/Antonio franco/Documents/IR/cral.csv', df.values())
                # df = {'title': [], 'authors': [], 'date': [],'journal': [], 'pages':[], 'conference': [],'publisher': [], 'description': [], 'num_citations': [], 'pdf_link': [], 'title_link': []}
                #driver.execute_script("window.history.go(-2)")
                        driver.back()
                        time.sleep(0.5)

            #driver.execute_script("window.history.go(-2)")
            driver.back()
            # time.sleep(1)
            # driver.refesh()
            time.sleep(0.5)
            #driver.back()
            #print(link)
        #time.sleep(1)
        bt=driver.find_elements_by_xpath('//*[@id="gsc_authors_bottom_pag"]/div/button[2]')[0]
        bt.click()
        time.sleep(0.5)

        print("Navigating to Next Page")
    except (TimeoutException, WebDriverException) as e:
        print("No completed")
        break
# driver.quit()


