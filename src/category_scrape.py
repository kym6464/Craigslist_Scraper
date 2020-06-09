"""
Scrape posts for a category under the "for sale" section - e.g. "cell phones".
"""
import json
from pathlib import Path

from src.query_post import get_post_data
from src.scrape_post import get_post_details
from src.utils import make_soup, get_timestamp

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

# ========================================== WORKERS =============================================
def get_post_overviews(url: str) -> list:
    """
    Get post overview information for a given URL.
    :param url: Craigslist search result page
    :return: [{title, link, ...}] high-level post info
    """
    soup = make_soup(url)
    posts = soup.find_all('li', class_='result-row')
    post_data = get_post_data(posts)
    return post_data


# ============================================ MAIN ==============================================


if __name__ == '__main__':
    category = 'cell phones'
    url = build_url(category)
    print(f"searching URL: {url}")

    # get search results
    posts = get_post_overviews(url)
    # write search results
    # TODO append timestamp using get_timestamp() to avoid over-writing
    filename = f"{category}.json"
    out_path = out_dir.joinpath('post_overview', filename)
    write_data(posts, out_path)

    # follow each search result to get details
    posts = posts[:5]  # TEMP
    post_details = [get_post_details(p['link']) for p in posts]
    # update each post with detail results
    for i,detail in enumerate(post_details):
        posts[i].update(detail)
    # Write posts, which now include overview and detailed info.
    out_path = out_dir.joinpath('post_detail', filename)
    write_data(posts, out_path)
