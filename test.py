
import sqlite3 as lite
from urllib.parse import urlsplit, urlunsplit
import json
import domain_utils
import csv 
import xml.etree.ElementTree as ET

with open("./scripts.json") as f:
    scripts = json.load(f)

DB_DIR = "./datadir/crawl-data.sqlite"
SOURCE_DUMP_DIR = "./datadir/sources/"
openwpm_db = DB_DIR
conn = lite.connect(openwpm_db)
cur = conn.cursor()
test_script_urls = ["https://cm.g.doubleclick.net/pixel?google_nid=bluekai&google_cm&google_sc&google_hm=cVFpZy9lUDk5eE8zSUVoaQ%3D%3D&", "https://c.bing.com/c.gif?uid=DuV3%2F9o%2B99OPNeNi&Red3=MSBK_pd", "https://analytics.twitter.com/i/adsct?type=javascript&version=2.0.13&p_id=Twitter&p_user_id=0&txn_id=o1apk&events=%5B%5B%22pag", "https://t.co/i/adsct?type=javascript&version=2.0.13&p_id=Twitter&p_user_id=0&txn_id=o1apk&events=%5B%5B%22pageview%22%2"]
script_urls = []


sitemap = ET.parse('sitemap.xml')
root = sitemap.getroot()
print(root.findall('.//loc'))
# pmcid = article.attrib.get('pmcid')
# for loc in article.findall('url/loc'):
#     print (loc)

    
with open('scripts.csv', 'a', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',')
    for url, site_url in cur.execute("SELECT DISTINCT s.site_url, v.url FROM site_visits s JOIN http_requests as v ON s.visit_id = v.visit_id ORDER BY s.site_url;"):
    # for site_url in test_script_urls:
        # print("url: ", url, " ; site_url: ", site_url)
        # print("site_url: " + site_url)
        
        subparts = domain_utils.hostname_subparts(site_url)
        script_base_domain = subparts[len(subparts)-1]
        for company_data in scripts:
            company_domains =  company_data["domains"]
            if (script_base_domain in company_domains) or ("*."+script_base_domain in company_domains):
                script_urls.append(dict(name=company_data["name"], script_base_domain=script_base_domain, categories=company_data["categories"]))
                # print("company data " + json.dumps(company_data))
                print("-----------------")
                print("Script Name: " + company_data["name"])
                print("Script Base Domain:" + script_base_domain)
                print("Full Script URL: " + site_url)
                print("Script Categories: " + ','.join(company_data["categories"]))
                print("Found In URL: " + url)
                print("-----------------")
                csvwriter.writerow([company_data["name"], script_base_domain, site_url, ','.join(company_data["categories"]),url])
                
    

# for url, site_url in cur.execute("SELECT DISTINCT s.site_url, v.script_url FROM site_visits s JOIN javascript as v ON s.visit_id = v.visit_id ORDER BY s.site_url;"):
#     print("url: ", url, " ; site_url: ", site_url)
   