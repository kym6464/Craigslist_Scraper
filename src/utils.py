import re
import unicodedata
import datetime
import requests
from bs4 import BeautifulSoup
from pathlib import Path


def get_project_root() -> Path:
    """Returns project root folder."""
    return Path(__file__).parent.parent


def to_valid_filename(value: str, lowercase=False, allow_unicode=False) -> str:
    """
    Convert string to a valid filename using simplified version of Django's
    "slugify" function.

    Convert spaces or repeated dashes to single dashes. Remove characters that
    aren't alphanumerics, underscores, or hyphens. Also strip leading and
    trailing whitespace, dashes, and underscores.
    :param lowercase: Convert to lowercase if 'lowercase' is True.
    :param value: string to make a valid filename from.
    :param allow_unicode: Convert to ASCII if 'allow_unicode' is False.
    :return valid filename.
    """
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    if lowercase:
        value = value.lower()
    value = re.sub(r'[^\w\s-]', '', value)
    return re.sub(r'[-\s]+', '-', value).strip('-_')


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
