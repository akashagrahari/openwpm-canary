from pathlib import Path

from custom_command import FormParserCommand
from openwpm.command_sequence import CommandSequence
from openwpm.commands.browser_commands import GetCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.task_manager import TaskManager
from sites import Sites
import sqlite3 as lite
import time
import json
import xmltodict
from datetime import datetime
import json
import script_finder

NUM_BROWSERS = 10
SITES_XML_PATH = "sitemap.xml" 

def get_sites(path):
    pages = []
    with open(path) as xml_file:
        data_dict = xmltodict.parse(xml_file.read())
        urls = data_dict['urlset']['url']
        for url in urls:
            pages.append(dict(url = url['loc'], dateDetected = int(time.time()), status = "new"))
    return pages

# The list of sites that we wish to crawl
sites = get_sites(SITES_XML_PATH)
site_urls = [site['url'] for site in sites]
print(site_urls)
print("Wrote site URLs to file")
with open('pages.json_{date}'.format(date = datetime.now().strftime("%m_%d_%Y_%H:%M:%S")), 'w+', encoding='utf-8') as outfile:
        json.dump(sites, outfile, ensure_ascii=False, indent=4)

# Loads the default ManagerParams
# and NUM_BROWSERS copies of the default BrowserParams

manager_params = ManagerParams(num_browsers=NUM_BROWSERS)
browser_params = [BrowserParams(display_mode="headless") for _ in range(NUM_BROWSERS)]

# Update browser configuration (use this for per-browser settings)
for browser_param in browser_params:
    # Record HTTP Requests and Responses
    browser_param.http_instrument = True
    # Record cookie changes
    browser_param.cookie_instrument = True
    # Record Navigations
    browser_param.navigation_instrument = True
    # Record JS Web API calls

    browser_param.js_instrument = True
    # Record the callstack of all WebRequests made
    browser_param.callstack_instrument = True
    # Record DNS resolution
    browser_param.dns_instrument = True

# Update TaskManager configuration (use this for crawl-wide settings)
manager_params.data_directory = Path("./datadir/")
manager_params.log_path = Path("./datadir/openwpm.log")

# memory_watchdog and process_watchdog are useful for large scale cloud crawls.
# Please refer to docs/Configuration.md#platform-configuration-options for more information
# manager_params.memory_watchdog = True
# manager_params.process_watchdog = True


# # Commands time out by default after 60 seconds
FORMS_DB_DIR = "./datadir/forms.sqlite"
conn = lite.connect(FORMS_DB_DIR)
cur = conn.cursor()
cur.execute('''DROP TABLE IF EXISTS forms;''')
cur.execute(''' CREATE TABLE IF NOT EXISTS forms
  (
     id   TEXT UNIQUE,

     element_id  TEXT,
     element_id_type TEXT,
     element_text   TEXT,
     element_tag    TEXT,
     pages  TEXT
  );''')



conn.commit()


with TaskManager(
    manager_params,
    browser_params,
    SQLiteStorageProvider(Path("./datadir/crawl-data.sqlite")),
    None,
) as manager:
    # Visits the sites
    count = site_urls
    for index, site in enumerate(site_urls):
        print("scanning site - ")
        def callback(success: bool, val: str = site) -> None:
            print(
                f"CommandSequence for {val} ran {'successfully' if success else 'unsuccessfully'}"
            )

        # Parallelize sites over all number of browsers set above.
        command_sequence = CommandSequence(
            site,
            site_rank=index,
            callback=callback,
        )
        # command_sequence.get()
        # command_sequence.browse(num_links=2, sleep=20, timeout=60)
        # Start by visiting the page
        command_sequence.append_command(GetCommand(url=site, sleep=0.5), timeout=60)
        # Have a look at custom_command.py to see how to implement your own command
        # command_sequence.append_command(LinkCountingCommand())
        formParser = FormParserCommand(site)
        command_sequence.append_command(formParser)
        # Run commands across all browsers (simple parallelization)
        manager.execute_command_sequence(command_sequence)

output = []
epoch_time = int(time.time())
for id, element_id, element_id_type, element_text, element_tag, pages in cur.execute("SELECT * FROM forms;"):
    pagesList = json.loads(pages)
    for page in pagesList:
        print("Appending form to file. Form ID: " + str(element_id))
        output.append({"formID": element_id, "formIDType": element_id_type, "formIDTag": element_tag, "formText": element_text, "dateDetected": epoch_time, "privacyPolicyExists": False, "url": page, "status": "new"})
conn.close()

with open('forms_{}.json'.format(epoch_time), 'w') as outfile:
    json.dump(output, outfile)
print("Dumped forms to file")

script_finder.find_scripts()

