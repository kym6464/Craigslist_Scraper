"""
Downloads the cities for each state in the US, as recognized by Craiglist.
"""
import json
import logging
import sys
import argparse
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, ParseResult
from src.utils import update_dict

# ========================================== Constants ===========================================
states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

# pattern used as sanity check on craigslist url before extracting city
url_pattern = re.compile(r"[\w]+\.craigslist\.org")

# base url pattern for listing cities within a state
base_url_parts = {k: '' for k in ['scheme', 'netloc', 'path', 'params', 'query', 'fragment']}
base_url_parts.update({
    'scheme': 'http',
    'netloc': 'geo.craigslist.org',
    'path': '/iso/us/{state}',
})


# =========================================== Helpers ============================================
def construct_url(state: str) -> str:
    """
    Construct URL for webpage showing list of cities
    :param state: the state to show cities for
    :return: url
    """
    path = base_url_parts['path'].format(state=state)
    url_parts = update_dict(base_url_parts, path=path)
    url = ParseResult(**url_parts).geturl()
    return url


def has_redirect(response: requests.Response) -> bool:
    """ Check if a response has a redirect in its history """
    return any([r.status_code == 302 for r in response.history])


def show_results(results):
    """ Show results as JSON """
    results_dict = {}
    for st, cityname_urls in results.items():
        city_urls = {cu[0]: cu[1] for cu in cityname_urls}
        results_dict[st] = city_urls

    print(json.dumps(results_dict, indent=4))


# =========================================== Core ===============================================
def extract_city(url: str) -> str:
    """
    Extract city name from Craigslist URL
    :raises TypeError if given url is improper format
    :param url: to extract city from
    :return: city
    """
    parts = urlparse(url)
    netloc = parts.netloc
    if not url_pattern.match(netloc):
        raise TypeError(f"Invalid URL to extract city from: {url}")
    city = netloc.split('.')[0]
    return city


def get_city_links(state: str) -> list:
    # download page for this state
    url = construct_url(state)
    response = requests.get(url)

    # redirect means this state has a single page
    if has_redirect(response):
        name = extract_city(response.url)
        return [(name, response.url)]

    # otherwise look for the URLs of each city
    soup = BeautifulSoup(response.content, 'lxml')
    lines = soup.body.div.section.div.ul
    cityname_link = [(a.get_text(), a['href']) for a in lines.findAll('a', href=True)]
    return cityname_link


def main():
    results = {}
    for st in states:
        try:
            city_links = get_city_links(st)
            results[st] = city_links
        except Exception:
            logging.error(f"Error for state: {st}", exc_info=True)
    show_results(results)


if __name__ == '__main__':
    desc = 'Get cities grouped by state, as recognized by Craigslist'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('file', default=False, nargs='?',
                        help='File to write results to. Otherwise prints to stdout')
    args = parser.parse_args()

    # redirect stdout to file
    if args.file:
        sys.stdout = open(args.file, 'w+')

    main()
