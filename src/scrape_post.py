import argparse
import pathlib
import json
from typing import List
from multiprocessing import Pool
from urllib.parse import urlparse
from bs4 import BeautifulSoup, NavigableString, Tag
from src.utils import make_soup


def get_city(url):
    """ Extract city information from URL """
    o = urlparse(url)
    city = o.netloc.split('.')[0]
    return city


def get_description(soup: BeautifulSoup) -> str:
    """
    Extract description from a post.
    :param soup: of post details page
    :return: description text
    """
    children = soup.body.section.section.section.section.children
    strings = [c for c in children if isinstance(c, NavigableString)]
    desc = ''.join(strings)
    return desc


def get_attributes(soup: BeautifulSoup) -> dict:
    """
    Extract attributes from a post.
    :param soup: of post details page
    :return: {condition, make/manufacturer, mobileOS, ...}
    """
    attributes = soup.find_all('p', 'attrgroup')
    if not attributes:
        return {}
    attributes = attributes[0]
    # extract field,value pairs
    field_value = {}
    for attr in attributes:
        if isinstance(attr, Tag):
            text = attr.get_text(strip=True)
            if len(text) == 0:
                continue
            parts = text.split(':')
            if len(parts) == 0:
                continue
            if len(parts) == 1:
                field, value = parts[0], None
            elif len(parts) == 2:
                field, value = parts
            else:
                field, value = parts[0], parts[1:]
            field_value[field] = value
    return field_value


def get_images(soup: BeautifulSoup) -> List[str]:
    """
    Extract image URLs from a post.
    :param soup: of post details page
    :return: [url] if 1 or more images found, otherwise []
    """
    # Grab list of images. Only works with posts which have a scrollable
    # gallery (e.g. 2 or more images)
    images = soup.find_all('a', {'data-imgid': True})
    image_urls = [e['href'] for e in images]
    # If there is no scrollable gallery, there may still be a single image.
    if not image_urls:
        first_visible = soup.find('div', {'class': 'slide first visible'})
        if first_visible:
            main_image = first_visible.find('img')
            if main_image:
                url = main_image.get('src')
                if url:
                    image_urls.append(url)
    return image_urls


def get_post_details(url: str) -> dict:
    """
    Extract details from a craigslist post link.
    :param url: Link to a post
    :return: {title, price, ...}
    """
    city = get_city(url)
    soup = make_soup(url)
    desc = get_description(soup)
    attributes = get_attributes(soup)
    images = get_images(soup)
    pd = {
        'city': city,
        'description': desc,
        'attributes': attributes,
        'images': images
    }
    return pd


def scrape_all_posts(data):
    post_links = [d['link'] for d in data]
    with Pool() as p:
        all_post_data = p.map(get_post_details, post_links)
    return all_post_data


def join_data(dicts1, dicts2):
    # same size lists as input
    for i,d1 in enumerate(dicts1):
        d1.update(dicts2[i])
    return dicts1


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Scrape individual postings")
    parser.add_argument('--input_dir', '-i', required=True,
                        help='Path to JSON files containing metadata about post')
    parser.add_argument('--out_dir', '-o', default='Data/Posting_Response')
    args = parser.parse_args()
    input_dir = pathlib.Path(args.input_dir)
    out_dir = pathlib.Path(args.out_dir)
    # folder or single file
    if input_dir.is_dir():
        files = input_dir.rglob("*.json")
    else:
        files = [input_dir]

    for fpath in files:
        # read data
        with open(fpath, 'r') as f:
            data = json.load(f)
        # run scraping
        data_ = scrape_all_posts(data)
        # join results
        data_result = join_data(data, data_)
        # write result
        out_fpath = out_dir.joinpath(fpath.name)
        with open(out_fpath, 'w') as f:
            json.dump(data_result, f, indent=2)
