import xmltodict
from datetime import datetime
import time
import site_list
import json

SITES_XML_PATH = "sitemap.xml" 
IMPORT_SITEMAP = False

def get_sites_urls_from_sitemap(path):
    with open(path) as xml_file:
        data_dict = xmltodict.parse(xml_file.read())
        urls = data_dict['urlset']['url']['loc']      
    return urls

def get_detailed_sites(site_urls):
    pages = []
    for url in site_urls:
            pages.append(dict(url=url, dateDetected = int(time.time()), status = "new"))
    return pages

def get_sites():
    if IMPORT_SITEMAP:
        print("getting sites from sitemap")
        site_urls = get_sites_urls_from_sitemap(SITES_XML_PATH)
    else:
        print("getting sites from sites list file")
        site_urls = site_list.Sites.SITES
        # print(site_urls)
    sites = get_detailed_sites(site_urls)
    return sites

def get_site_urls():
    sites = get_sites()
    site_urls = [site['url'] for site in sites]
    return site_urls

def save_pages():
    # The list of sites that we wish to crawl
    sites = get_sites()
    with open('pages.json_{date}'.format(date = datetime.now().strftime("%m_%d_%Y_%H:%M:%S")), 'w+', encoding='utf-8') as outfile:
            json.dump(sites, outfile, ensure_ascii=False, indent=4)
    print("Wrote site URLs to file")
    return sites