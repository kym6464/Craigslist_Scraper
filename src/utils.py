import datetime
import requests
from bs4 import BeautifulSoup
from pathlib import Path


def get_project_root() -> Path:
    """Returns project root folder."""
    return Path(__file__).parent.parent


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


def get_timestamp() -> str:
    """ Get current datetime for appending to filename """
    return datetime.datetime.now().strftime("%d-%m-%Y_%I-%M-%S%p")
