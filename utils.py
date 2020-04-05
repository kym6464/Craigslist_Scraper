import requests
from bs4 import BeautifulSoup


def make_soup(url):
    """ Download URL, package as Soup """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'lxml')
    return soup


def strip_html_tags(text):
    """remove html tags from text"""
    soup = BeautifulSoup(text, "lxml")
    stripped_text = soup.get_text(separator=" ")
    return stripped_text