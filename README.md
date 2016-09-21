# Scraper
This Scraper class is built using the selenium webdriver class. It's most basic functions scrape all links from the webpage, and recurses through the links to build a site map. The Scraper object is initiated with an unused webdriver object, an empty site map, an empty visited list and an empty to_visit Queue.

##Current Changes
1. add a page_context function to extract relevant information
2. 

##Package Requirements:
- bs4
- Queue
- selenium
- pprint
- pandas
- re
- pickle
- time

##Function list:
- scrape_page, given page definition visit page and scrape links
- create_driver
- push_page, adds a page to the to_visit queue
- define_page, creates the parent child key pair and adds relevant context
- get_url, fetches the absolute url from a page definition
- make_url, given any form of a href link, return an absolute url
- 
