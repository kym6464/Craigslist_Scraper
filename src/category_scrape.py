"""
Scrape posts for a category under the "for sale" section - e.g. "cell phones".
"""
import asyncio
import json
from pathlib import Path

import aiohttp

from bs4 import BeautifulSoup
from src.query_post import extract_overview_info
from src.scrape_post import get_city, get_description, get_attributes
from src.utils import get_timestamp

# ========================================== CONSTANTS ===========================================
# directory for overview and detail posts
out_dir = Path(r'../data/category')

# base URL for search by "for sale" category
net_loc = r'https://lancaster.craigslist.org'  # TEMP
base_url = net_loc + r'/d/{catName}/search/{catAbbr}'

# read category names and abbreviations
file_abbreviations = '../config/category_abbreviations.json'
with open(file_abbreviations, 'r') as f:
    cat_abbr = json.load(f)

# ========================================== HELPERS =============================================
def build_url(category):
    """
    Build URL for a given category under the "for sale" section.
    :param category: a category under the "for sale" section of Craigslist
    :return: URL string
    """
    # grab category abbreviation
    abbr = cat_abbr[category]
    # replace space with `-`
    category = category.replace(' ', '-')
    url = base_url.format(catName=category, catAbbr=abbr)
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
    # TODO worth parallelizing this step?
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
    pd = {
        'city': city,
        'description': desc,
        'attributes': attributes
    }
    return pd


# ============================================ MAIN ==============================================
async def main():
    category = 'cell phones'
    url = build_url(category)
    print(f"searching URL: {url}")

    # initialize HTTP session
    session = aiohttp.ClientSession()

    # get search results
    posts = await get_post_overviews(url, session)
    # write search results
    # TODO append timestamp using get_timestamp() to avoid over-writing
    filename = f"{category}.json"
    out_path = out_dir.joinpath('post_overview', filename)
    write_data(posts, out_path)

    # follow each search result to get details
    tasks = [asyncio.create_task(get_post_details(p['link'], session)) for p in posts]
    post_details = await asyncio.gather(*tasks)
    # update each post with detail results
    for i,detail in enumerate(post_details):
        posts[i].update(detail)
    # Write posts, which now include overview and detailed info.
    out_path = out_dir.joinpath('post_detail', filename)
    write_data(posts, out_path)

    # close HTTP session
    await session.close()


if __name__ == '__main__':
    # run the program
    asyncio.run(main())
