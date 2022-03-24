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

DB_DIR = "./datadir/crawl-data.sqlite"
SOURCE_DUMP_DIR = "./datadir/sources/"
openwpm_db = DB_DIR
conn = lite.connect(openwpm_db)
cur = conn.cursor()


for url, site_url in cur.execute("SELECT DISTINCT h.url, v.script_url FROM http_requests h JOIN javascript as v ON h.visit_id = v.visit_id;"):
    print("url: ", url, " ; site_url: ", site_url)
   