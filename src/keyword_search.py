import pathlib
import requests
from lxml import etree
from datetime import datetime
import json

# directory to write file
out_dir = r"Data/Query_Response"
# search string
query = input('Search: ')

# run query
url = f'https://lancaster.craigslist.org/search/sss?format=rss&query={query}&sort=rel'
response = requests.get(url)
if response.status_code != 200:
    raise ConnectionError('response code != 200')
root = etree.fromstring(response.content)

# parse results
items = []
for item in root.findall('item', root.nsmap):
    tags = [elt.tag for elt in item]
    fields = [t.split('}')[1] for t in tags]
    values = [elt.text for elt in item]
    entry = dict(zip(fields, values))
    items.append(entry)

# write to file
time = datetime.now().strftime("%d-%m-%Y_%I-%M-%S_%p")
filename = f"{query}_{time}.json"
fpath = pathlib.Path(out_dir).joinpath(filename)
with open(fpath, 'w') as f:
    json.dump(items, f, indent=True)
