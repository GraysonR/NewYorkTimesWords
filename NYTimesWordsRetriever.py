#!/usr/bin/python
__author__ = 'Grayson Ricketts'

from BeautifulSoup import BeautifulSoup
from tidylib import tidy_document
import requests
import datetime
import time
import nltk
from nltk import word_tokenize
import operator
from config import connect_to_server



"""""New York Times Words Retriever
Using the NYTimes API, comb through all the articles published on a day and
count the occurrence of each word.
"""""

def create_date_string(date):
    """ Creates a data string from a datetime object 
    """

    # Make month a string and add 0 to front if necessary
    month = str(date.month)
    if len(month) == 1:
        month = '0' + str(month)

    # Make day a string and add 0 to front if necessary
    day = str(date.day)
    if len(day) == 1:
        day = '0' + str(day)

    return str(date.year) + month + day

def get_article_urls(date):
    """ Gets the all the working URLs for a specific day and returns the URLs
    in a list.
    """

    # List that will hold the days worth of URLs
    urls = []

    # API key and page number initialized
    api_key = #insert API key here
    page = 0

    date_string = create_date_string(date + datetime.timedelta(days=1))

    # Loops through and gets all the URLs of a specific day
    while 1:
        jsonurl = 'http://api.nytimes.com/svc/search/v2/articlesearch.json?' \
                  '&fq=news_desk:("national"+"world"+"politics")AND' \
                  'source=("The+New+York+Times")' \
                  '&begin_date=' + str(date_string) + '&end_date=' + str(date_string) + \
                  '&fl=web_url' \
                  '&page=' + str(page) + '&api-key=' + api_key

        # Opens the url and loads the JSON
        req = requests.get(jsonurl)
        data = req.json()

        # Exits loop when there are no more urls
        if len(data['response']['docs']) == 0:
            break

        # Gets the URLs within the response by iterating through the sub list
        # and getting the values of web_url
        urls.extend(u['web_url'] for u in data['response']['docs'])

        # Gets the next page of URLs and waits so that the time max number of
        # requests per second of the API is not overwhelmed
        page += 1
        time.sleep(.1)

    return urls


def count_words(urls):
    """Cleans an article keeping only nouns, verbs, adjectives, and adverbs.
    Returns a dictionary with the words as values and the frequency of each
    word as the keys.
    """
    # Dictionary that will hold all the words and their associated count
    daily_words = {}

    # Goes through a days worth of URLs. Cleans, tockenizes, and counts each
    # article. Each article's words are then merged into the daily_words.
    for link in urls:
        # Opens the page with the link and tidies the text and gets the page
        # ready to be parsed.
        page = requests.get(link)
        tidy, errors = tidy_document(page.text)
        soup = BeautifulSoup(tidy)

        # If the page no longer exists then go to the next URL
        if soup.title.name == 'Page Not Found':
            continue

        # Goes through the page and picks out the article
        article = ""
        for body in soup.findAll('p', {'itemprop': 'articleBody'}):
            article += body.text

        # Cleans the article
        article = article.replace('.', ' ')
        article = article.replace('\'', ' ')

        # Cleans the article leaving only the words most relevant
        # to be added to the daily words dict.
        text = word_tokenize(article)
        tags = nltk.pos_tag(text)
        words = [word for (word, tag) in tags if tag == 'NN' or tag == 'NNP'
                    or tag == 'NNS' or tag == 'VBN' or tag == 'VBD'
                    or tag == 'CD' or tag == 'RB' or tag == 'JJ']

        # Adds the words of the article to the daily word count dictionary
        for w in words:
            # Skip anomalies or unimportant small words
            if len(w) <= 2:
                continue

            w = w.upper()
            if daily_words.__contains__(w):
                daily_words[w] += 1
            else:
                daily_words[w] = 1

    # Clean it a bit more.
    bad_words = ['THE', 'WAS', 'NOT', 'HAD', 'WERE', 'BEEN', 'EVEN', 'ALSO', 
                'MANY', 'SAID']
    for word in words:
        try:
            list.remove(word)
        except:
            pass

    # Sorts the words by frequency and then returns the top 125
    daily_words = sorted(daily_words.items(), key=operator.itemgetter(1), reverse=True)[:200]

    return daily_words


def store_words(words, date, link):
    """Stores the words and counts associated with a date in a mySQL database."""

    # Creates a cursor
    cursor = link.cursor()

    # Add date format
    add_date = ("INSERT INTO words "
               "(Word, Count, Date) "
               "VALUES (%s, %s, %s)")

    # Goes through the days words and enters them into the database
    for (word, count) in words:
        data_date = (word, count, date)
        cursor.execute(add_date, data_date)



    # Closes the cursor
    cursor.close()

    return