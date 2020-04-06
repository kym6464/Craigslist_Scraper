import requests
from bs4 import BeautifulSoup


def update_dict(base: dict, **kwargs) -> dict:
    """ Update base dict and return result dict, without modifying original """
    base_cpy = base.copy()
    base_cpy.update(kwargs)
    return base_cpy


def make_soup(url):
    """ Download URL, package as Soup """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'lxml')
    return soup


def strip_html_tags(text):
    """ remove html tags from text """
    soup = BeautifulSoup(text, "lxml")
    stripped_text = soup.get_text(separator=" ")
    return stripped_text
