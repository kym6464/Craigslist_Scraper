import argparse
import pathlib
import json
from datetime import datetime
from src.utils import make_soup

# CONSTANTS
city = 'lancaster'
cat = 'moa'  # cell phones
base_url = 'https://' + city + '.craigslist.org/search/' + cat + '?query={}&sort=rel&bundleDuplicates=1'


def create_url(query):
    words = query.split()
    param = '+'.join(words)
    url = base_url.format(param)
    return url


def extract_overview_info(search_result_post):
    """
    Extract overview information from a search result post entry.
    :param search_result_post: A single post search result
    :return: {title, link, pid, ...}
    """
    # extract data
    title_attr = search_result_post.find('a', class_='result-title hdrlnk')
    link = title_attr['href']
    title = title_attr.get_text()
    pid = search_result_post['data-pid']
    pid_repost = search_result_post['data-repost-of'] if 'data-repost-of' in search_result_post.attrs else None
    price_str = search_result_post.find(class_='result-price').get_text(strip=True)
    price = int(''.join([p for p in price_str if p.isdigit()]))
    time = search_result_post.find('time', class_='result-date')['datetime']
    # save data
    entry = {
        'title': title,
        'link': link,
        'pid': pid,
        'pid_repost': pid_repost,
        'price': price,
        'time': time
    }
    return entry


def get_post_data(posts):
    post_data = []
    for p in posts:
        entry = extract_overview_info(p)
        post_data.append(entry)
    return post_data


def scrape_posts(query):
    url = create_url(query)
    soup = make_soup(url)
    posts = soup.find_all('li', class_='result-row')
    post_data = get_post_data(posts)
    return post_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Get posts for a given keyword")
    parser.add_argument('query',
        help='Keyword to search')
    parser.add_argument('--out_dir', '-o', default='Data/Query_Response',
        help='Dir to write results to')
    args = parser.parse_args()
    query = args.query
    out_dir = pathlib.Path(args.out_dir)

    # query posts
    post_data = scrape_posts(query)

    # write result
    time = datetime.now().strftime("%d-%m-%Y_%I-%M-%S_%p")
    filename = f"{query}_{time}.json"
    fpath = pathlib.Path(out_dir).joinpath(filename)
    with open(fpath, 'w') as f:
        json.dump(post_data, f, indent=True)
