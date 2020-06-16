"""
Scrape posts for a category under the "for sale" section - e.g. "cell phones" - for given state
and city.
"""
import asyncio
import json
from typing import Tuple

import aiohttp

from bs4 import BeautifulSoup
from src.query_post import extract_overview_info
from src.scrape_post import get_city, get_description, get_attributes, get_images
from src.utils import get_project_root, get_timestamp, to_valid_filename

# ========================================== CONSTANTS ===========================================
# root directory
root_dir = get_project_root()

# directory for overview and detail posts
out_dir = root_dir.joinpath('data/category')

# base URL for search by "for sale" category
url_path_template = r'{baseUrl}/d/{catName}/search/{catAbbr}'

# read state,city --> URL mapping
location_urls = root_dir.joinpath('config/city_url_by_state.json')
with open(location_urls, 'r') as f:
    state_city_to_url = json.load(f)

# read category names and abbreviations
file_abbreviations = root_dir.joinpath('config/category_abbreviations.json')
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


async def write_results(state: str, city: str, category: str,
                        post_overviews: list, post_details: list) -> None:
    """ Write result posts to files. """
    # Ensure all values are compatible with a Path.
    state, city, category = map(to_valid_filename, [state, city, category])
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


async def scrape_category_state(state: str, category: str) -> dict:
    """
    Scrape all posts in a category within all cities in the given state.
    :param state: State abbreviation.
    :param category: a 'for sale' category, e.g. 'cell phones'
    :return: {city_name: ( [post_overview], [post_detail] )}
    """
    # Validate input argument
    city_to_url = state_city_to_url.get(state, None)
    if not city_to_url:
        raise ValueError(f"Invalid state abbreviation: {state}")
    # Run for each city
    cities = list(city_to_url.keys())
    tasks = [asyncio.create_task(scrape_category_location(state, city, category))
             for city in cities]
    # Package result per-city. From the docs: "The order of result values
    # corresponds to the order of awaitables".
    results = await asyncio.gather(*tasks)
    city_result = {cities[i]: res for i,res in enumerate(results)}
    return city_result


async def scrape_category_all(category: str) -> Tuple[list, list]:
    """
    TODO due to memory limitations, this should not return all results at once.
    Scrape all posts in a category within all of the US.
    :param category: a 'for sale' category, e.g. 'cell phones'
    :return: ( [post_overview], [post_detail] )
    """
    pass


# ============================================ MAIN ==============================================
async def main(state, city, category):
    # If city is given, search only that city
    if city:
        # Get posts for this city.
        results = await scrape_category_location(state, city, category)
        city_results = {city: results}
    # Otherwise city is not given. Search all cities within the state.
    else:
        # Get posts for each city.
        city_results = await scrape_category_state(state, category)

    # Write results. NOTE: Performance hit of this step is insignificant
    # compared to previous step, so we do not need aiofiles.
    for city,(post_overviews, post_details) in city_results.items():
        await write_results(state, city, category, post_overviews, post_details)


if __name__ == '__main__':
    import argparse
    desc = "Scrape posts under a 'for sale' category, within a city."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('state', help='State abbreviation')
    parser.add_argument('city', nargs='?', help='City name within given state.'
        ' If excluded, will search all cities in state.')
    parser.add_argument('category', help="A 'for sale' category, e.g. 'electronics'")
    args = parser.parse_args()

    # run the program
    asyncio.run(main(args.state, args.city, args.category))
