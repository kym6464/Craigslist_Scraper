"""
TODO DEPRECATED
Process the raw scraped data by extracting relevant fields.
"""
import argparse
import pathlib
import json

from utils import strip_html_tags


def preprocess(data):
    for entry in data:
        entry['price'] = None
        if 'title' in entry:
            title = strip_html_tags(entry['title'])
            entry['title'] = title
            if '$' in title:
                entry['price'] = title.split('$')[1]
        if 'description' in entry:
            desc = strip_html_tags(entry['description'])
            entry['description'] = desc
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Process raw query responses.")
    parser.add_argument('--input_dir', '-i', required=True,
                        help='Path to JSON files')
    parser.add_argument('--out_dir', '-o', default='Data/Query_Processed')
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
        # run preprocessing
        data_ = preprocess(data)
        # write result
        out_fpath = out_dir.joinpath(fpath.name)
        with open(out_fpath, 'w') as f:
            json.dump(data_, f, indent=2)
