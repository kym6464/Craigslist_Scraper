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
