from re import S
import sys
from pathlib import Path
from custom_command import FormParserCommand, AllowCookiesCommand
from openwpm.command_sequence import CommandSequence
from openwpm.commands.browser_commands import GetCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.task_manager import TaskManager
import sqlite3 as lite
import time
import json
from pages_finder import get_site_urls, save_pages
import script_finder
import all_cookies_finder
from datetime import datetime
import argparse

NUM_BROWSERS = 10

parser = argparse.ArgumentParser(description='Scan and analyse')
parser.add_argument('--scan', type=bool, required=True, help='scan the provided urls', action=argparse.BooleanOptionalAction)
parser.add_argument('--analyse', type=bool, required=True, help='analyse the results and save to file', action=argparse.BooleanOptionalAction)
parser.add_argument('--pages', type=bool, required=True, help='fetch pages from urls', action=argparse.BooleanOptionalAction)
parser.add_argument('--forms', type=bool, required=True, help='fetch forms from urls', action=argparse.BooleanOptionalAction)
parser.add_argument('--scripts', type=bool, required=True, help='fetch scripts from urls', action=argparse.BooleanOptionalAction)
parser.add_argument('--all_cookies', type=bool, required=True, help='fetch all cookies from urls', action=argparse.BooleanOptionalAction)
parser.add_argument('--allow_ot_cookies', type=bool, required=True, help='Allow cookies for OneTrust banners', action=argparse.BooleanOptionalAction)
args = parser.parse_args()

SCAN = args.scan
ANALYSE = args.analyse
print("SCAN = " + str(SCAN))
print("ANALYSE = " + str(ANALYSE))
print("pages = " + str(args.pages))
print("forms = " + str(args.forms))
print("scripts = " + str(args.scripts))
print("all_cookies = " + str(args.all_cookies))
print("allow_ot_cookies = " + str(args.allow_ot_cookies))
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
manager_params.failure_limit = 10000000000000
# memory_watchdog and process_watchdog are useful for large scale cloud crawls.
# Please refer to docs/Configuration.md#platform-configuration-options for more information
# manager_params.memory_watchdog = True
# manager_params.process_watchdog = True

FORMS_DB_DIR = "./datadir/forms.sqlite"
conn = lite.connect(FORMS_DB_DIR)
cur = conn.cursor()

error_sites = []
site_urls = get_site_urls()

if SCAN == True:
    # # Commands time out by default after 60 seconds
    if args.forms:
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
        print("Scanning urls.......")
        # Visits the sites
        count = 0
        for index, site in enumerate(site_urls):
            print("-----------------scanning site - " +str(count) + " /" + str(len(site_urls)) + "--" + site)
            count+=1
            def callback(success: bool, val: str = site) -> None:
                print(
                    f"CommandSequence for {val} ran {'successfully' if success else 'unsuccessfully'}"
                )
                if not success:
                    error_sites.append(site)
            # Parallelize sites over all number of browsers set above.
            command_sequence = CommandSequence(
                site,
                site_rank=index,
                callback=callback,
            )
            # command_sequence.get()
            # command_sequence.browse(num_links=2, sleep=20, timeout=60)
            # Start by visiting the page


            command_sequence.append_command(GetCommand(url=site, sleep=1), timeout=60)

            if args.allow_ot_cookies:    
                allowCookiesCommand = AllowCookiesCommand()
                command_sequence.append_command(allowCookiesCommand, timeout=20)

            # Have a look at custom_command.py to see how to implement your own command
            # command_sequence.append_command(LinkCountingCommand())
            if args.forms:
                formParser = FormParserCommand(site)
                command_sequence.append_command(formParser, timeout=60)
            
            # Run commands across all browsers (simple parallelization)
            manager.execute_command_sequence(command_sequence)
            # print("-----------------finished scanning site - " + site)

if ANALYSE:
    print("analysing data")
    if args.pages:
        sites = save_pages()
    if args.forms:
        print("analysing forms...")
        forms_output = []
        epoch_time = int(time.time())
        for id, element_id, element_id_type, element_text, element_tag, pages in cur.execute("SELECT * FROM forms;"):
            pagesList = json.loads(pages)
            for page in pagesList:
                print("Appending form to file. Form ID: " + str(element_id))
                formData = {"formID": element_id, "formIDType": element_id_type, "formIDTag": element_tag, "formText": element_text, "dateDetected": epoch_time, "privacyPolicyExists": False, "url": page, "status": "new"}
                forms_output.append(formData)
        conn.close()

        with open('forms_{}.json'.format(epoch_time), 'w') as outfile:
            json.dump(forms_output, outfile)
        print("Dumped forms to file")

    if args.scripts:
        print("analysing scripts...")
        scripts = script_finder.find_scripts()

    if args.all_cookies:
        print("analysing all cookies...")
        all_cookies = all_cookies_finder.find_all_cookies()

    print("error sites")
    print(error_sites)

    with open('error_sites_{}.json'.format(epoch_time), 'w') as outfile:
        json.dump(error_sites, outfile)

    print("building full payload...")
    with open('payload_empty.json') as f:
        full_site_payload = json.load(f)
        domainData = full_site_payload["domains"][0]
        domainData["domainName"] = site_urls[0].removeprefix("https://").removesuffix("/")
        if args.pages: 
                domainData["tests"]["changeDetection"]["pages"] = sites
        
        if args.forms:
            domainData["tests"]["changeDetection"]["forms"] = forms_output
        
        if args.scripts:
            domainData["tests"]["changeDetection"]["scripts"] = scripts
        
        if args.all_cookies:
            domainData["tests"]["changeDetection"]["cookies"] = all_cookies
        
        with open('{domain_name}_{date}.json'.format(domain_name = domainData["domainName"], date = datetime.now().strftime("%m_%d_%Y_%H:%M:%S")), 'w+', encoding='utf-8') as outfile:
                json.dump(full_site_payload, outfile, ensure_ascii=False, indent=4)
                print("Dumped full paylaod to file for: "  + domainData["domainName"])