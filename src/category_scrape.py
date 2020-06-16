"""
Scrape posts for a category under the "for sale" section - e.g. "cell phones" - for given state
and city.
"""
import asyncio
import json
from pathlib import Path
from typing import Tuple

import aiohttp

from bs4 import BeautifulSoup
from src.query_post import extract_overview_info
from src.scrape_post import get_city, get_description, get_attributes, get_images
from src.utils import get_timestamp

# ========================================== CONSTANTS ===========================================
# directory for overview and detail posts
out_dir = Path(r'../data/category')

# base URL for search by "for sale" category
# net_loc = r'https://lancaster.craigslist.org'  # TEMP
url_path_template = r'{baseUrl}/d/{catName}/search/{catAbbr}'

# read state,city --> URL mapping
location_urls = '../config/city_url_by_state.json'
with open(location_urls, 'r') as f:
    state_city_to_url = json.load(f)

# read category names and abbreviations
file_abbreviations = '../config/category_abbreviations.json'
with open(file_abbreviations, 'r') as f:
    cat_abbr = json.load(f)

# ========================================== HELPERS =============================================
def build_url(base_url, category):
    """
    Build URL for a given category under the "for sale" section.
    :param category: a category under the "for sale" section of Craigslist
    :param base_url: URL to specific craiglist loc, e.g "lancaster.craigslist.org"
    :return: URL string
    """
    # grab category abbreviation
    abbr = cat_abbr[category]
    # replace space with `-`
    category = category.replace(' ', '-')
    url = url_path_template.format(baseUrl=base_url, catName=category, catAbbr=abbr)
    return url

def write_data(data, fp):
    with open(fp, 'w+') as f:
        json.dump(data, f, indent=2)

async def url_to_soup(url: str, session: aiohttp.ClientSession) -> BeautifulSoup:
    """ Download webpage, package as BeautifulSoup """
    async with session.get(url) as response:
        return BeautifulSoup(await response.text(), 'html.parser')

# ========================================== WORKERS =============================================
async def get_post_overviews(url: str, session: aiohttp.ClientSession) -> list:
    """
    Get post overview information for a given URL.
    :param url: Craigslist search result page
    :param session: HTTP session to use
    :return: [{title, link, ...}] high-level post info
    """
    soup = await url_to_soup(url, session)
    posts = soup.find_all('li', class_='result-row')
    # async version of next step did not affect performance (bc. cpu/mem bound)
    post_data = [extract_overview_info(p) for p in posts]
    return post_data


async def get_post_details(url: str, session: aiohttp.ClientSession) -> dict:
    """
    Extract details from a craigslist post link.
    :param url: Link to a post
    :param session: HTTP session to use
    :return: {title, price, ...}
    """
    city = get_city(url)
    soup = await url_to_soup(url, session)
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


# ============================================ API ===============================================
async def scrape_category(base_url: str, category: str) -> Tuple[list, list]:
    """
    Scrape all posts in a category, within given base url.
    :param base_url: specific CL link, e.g. lancaster.craigslist.org
    :param category: a 'for sale' category, e.g. 'cell phones'
    :return: ( [post_overview], [post_detail] )
    """
    url = build_url(base_url, category)
    print(f"searching URL: {url}")

    # Reuse single HTTP session.
    async with aiohttp.ClientSession() as session:
        # Get search results, which are posts.
        post_overviews = await get_post_overviews(url, session)
        # Follow each search result to get post details.
        tasks = [asyncio.create_task(get_post_details(p['link'], session)) for p in post_overviews]
        post_details = await asyncio.gather(*tasks)

    # Update each post with details.
    for i,detail in enumerate(post_details):
        detail.update(post_overviews[i])
    # Return results.
    return post_overviews, post_details


async def scrape_category_location(state: str, city: str, category: str) -> Tuple[list, list]:
    """
    Scrape all posts in a category within the state and city specified.
    :param state: State abbreviation.
    :param city: City within above state.
    :param category: a 'for sale' category, e.g. 'cell phones'
    :return: ( [post_overview], [post_detail] )
    """
    # Validate input arguments.
    state, city = state.upper(), city.lower()
    city_to_url = state_city_to_url.get(state, None)
    if not city_to_url:
        raise ValueError(f"Invalid state abbreviation: {state}")
    base_url = city_to_url.get(city, None)
    if not base_url:
        raise ValueError(f"City '{city}' not found in state '{state}'")

    # get base URL
    base_url = state_city_to_url[state][city]
    # return results
    return await scrape_category(base_url, category)


# ============================================ MAIN ==============================================
async def main(state, city, category):
    # Get posts.
    post_overviews, post_details = await scrape_category_location(state, city, category)

    # Initialize output directories.
    result_dir = out_dir.joinpath(category, state, city)
    result_dir.mkdir(parents=True, exist_ok=True)

    # Save post overviews.
    timestamp = get_timestamp()
    out_path_overview = result_dir.joinpath(f'{timestamp}_OVERVIEW.json')
    write_data(post_overviews, out_path_overview)
    # Save post detailed info.
    out_path_detail = result_dir.joinpath(f'{timestamp}_DETAIL.json')
    write_data(post_details, out_path_detail)

    # Log
    print(f"Saved overviews to:\t {out_path_overview}")
    print(f"Saved details to:\t {out_path_detail}")


if __name__ == '__main__':
    import argparse
    desc = "Scrape posts under a 'for sale' category, within a city."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('state', help='State abbreviation')
    parser.add_argument('city', help='City name within given state')
    parser.add_argument('category', help="A 'for sale' category, e.g. 'electronics'")
    args = parser.parse_args()

    # run the program
    asyncio.run(main(args.state, args.city, args.category))
