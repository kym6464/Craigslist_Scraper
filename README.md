# Craigslist_Scraper
Scrape data from Craigslist for data analysis.


## Category Scraping
The **Output Directory Structure** is as follows:
```
category
└── category_A
    └── state_A
        └── city_A
            ├── post_overview_Date_Time.json
            └── post_detail_Date_Time.json
    └── state_B
        └── city_B
            ├── post_overview_Date_Time.json
            └── post_detail_Date_Time.json
    ...
```


## Design Notes
Scraping is done in 2 steps:
1. Overview step - For a search URL, download the high-level post info (e.g. title, url) for each
post.
2. Detail step - For each post URL, navigate to it, and download the details of the post.

The process is split into 2 individual steps to support `caching` in the future. An obvious use case
is to pull down new posts without making uneccesary calls if we have already downloaded the details
of a post.

Also, this approach decouples the two steps which will make development and debugging easier in the future when handling data in bulk.


## Sensitive Identifiers
Some information is obtained using named identifiers that, if craigslist were to change, would break the code. This section lists those values for easier tracking.

`data-img-id` attribute is used to obtain image URLs from post details page.
* EX. 
```
 <a class="thumb" data-imgid="98xLfSGDIzq_0jm0t2" href="https://images.craigslist.org/00303_98xLfSGDIzq_0jm0t2_600x450.jpg" id="1_thumb_98xLfSGDIzq_0jm0t2" title="1"><img alt="1" class="selected" src="https://images.craigslist.org/00303_98xLfSGDIzq_0jm0t2_50x50c.jpg"/></a>,
```


## Images
The surface images are displayed at a resolution of **600 x 450**. Clicking on the image will enlarge it, usually making it **1200 x 900**. However, enlarging an image is not always available. The image URL encodes the size information, EX:
- https://images.craigslist.org/00o0o_5ej82vPO9kT_**600x450**.jpg
- https://images.craigslist.org/00o0o_5ej82vPO9kT_**1200x900**.jpg

The available sizes are listed in the javascript code, EX:
```javascript
var imageConfig = {
    "4": {
        "hostname": "https://images.craigslist.org", 
        "sizes":["50x50c","300x300","600x450","1200x900"]
        }
};
```

Because **600 x 450** is large enough for most image processing applications and because we prefer not to parse javascript code, we only take the lower-quality images. 

If higher quality images become necessary, a few **solutions**:
1. Parse the javascript code to get all available image URLs.
2. Try to modify the image sizes in the URL directly, and use brute-force to see which do not return a 404 error. This is probably easier since there are likely a small set of available image sizes.  


## TODO
Search category by:
1. [x] a city in a state 
2. [ ] every city in a state
3. [ ] every city in every state

Only write new results, by running diff against previous data within a category.
