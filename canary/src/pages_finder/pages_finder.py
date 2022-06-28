from numpy import full_like
import xmltodict
from datetime import datetime
import time
import json
from .site_list import Sites
import sys, os
import canary.src.utils.utils as utils

def get_sites_urls_from_sitemap(path):
    with open(path) as xml_file:
        data_dict = xmltodict.parse(xml_file.read())
        urls = data_dict['urlset']['url']
        locs = [url["loc"] for url in urls]
    return locs

def get_detailed_sites(site_urls):
    pages = []
    for url in site_urls:
            pages.append(dict(url=url, dateDetected = int(time.time()), status = "new"))
    return pages

def get_sites(sitemap_path = ''):
    if sitemap_path != '':
        print("getting sites from sitemap")
        site_urls = get_sites_urls_from_sitemap(sitemap_path)
    else:
        print("getting sites from sites list file")
        site_urls = Sites.SITES
        # print(site_urls)
    sites = get_detailed_sites(site_urls)
    return sites

def get_site_urls(page_limit = 0, sitemap_path = ''):
    sites = get_sites(sitemap_path=sitemap_path)
    site_urls = [site['url'] for site in sites]
    if page_limit > 0:
        site_urls = site_urls[0:page_limit]
    return site_urls

def save_pages(page_limit = 0, sitemap_path = '', domain=''):
    # The list of sites that we wish to crawl
    sites = get_sites(sitemap_path=sitemap_path)
    if page_limit > 0 :
        sites = sites[0:page_limit]
    file_name = 'scanned_pages_{domain}_{date}.json'.format(date = datetime.now().strftime("%m_%d_%Y_%H:%M:%S"), domain = domain)
    file_path = './canary/output/pages/' + file_name
    with open(file_path, 'w+', encoding='utf-8') as outfile:
            json.dump(sites, outfile, ensure_ascii=False, indent=4)
    utils.upload_file_to_s3("canary-scanned-pages", file_path, file_name, is_public=False)
    print("Wrote site URLs to file")
    return sites

# save_pages(page_limit = 0, sitemap_filename = 'sitemap_talia')
# get_site_urls(page_limit=50, import_sitemap=True)