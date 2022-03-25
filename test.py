import site
import sqlite3 as lite
from urllib.parse import urlsplit, urlunsplit
import json
import gzip
import os
from bs4 import BeautifulSoup
import re
import urllib
import urllib.request
import requests
from pprint import pprint

DB_DIR = "./datadir/crawl-data.sqlite"
SOURCE_DUMP_DIR = "./datadir/sources/"
openwpm_db = DB_DIR
conn = lite.connect(openwpm_db)
cur = conn.cursor()


# for site_url, script_url in cur.execute("SELECT DISTINCT s.site_url, v.script_url FROM site_visits s JOIN javascript as v ON s.visit_id = v.visit_id ORDER BY s.site_url;"):
#     print(site_url, ",", script_url)
   
# pprint(cur.execute("SELECT * FROM javascript_cookies;").fetchall())

for site_url, script_url in cur.execute("SELECT DISTINCT s.site_url, v.url FROM site_visits s JOIN http_requests as v ON s.visit_id = v.visit_id ORDER BY s.site_url;"):
    print(site_url, ",", script_url)