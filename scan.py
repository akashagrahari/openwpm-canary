from email import utils
from re import S
from datetime import datetime
from pathlib import Path
import sqlite3 as lite
import time
import json
from openwpm.command_sequence import CommandSequence
from openwpm.commands.browser_commands import GetCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.task_manager import TaskManager
from canary.src.custom_commands.custom_commands import FormParserCommand, AllowCookiesCommand
from canary.src.pages_finder.pages_finder import get_site_urls, save_pages
import canary.src.script_finder.script_finder as script_finder
import canary.src.all_cookies_finder.all_cookies_finder as all_cookies_finder
import canary.src.cookie_enhancer.cookie_enhancer as cookie_enhancer
import canary.src.utils.utils as utils
import canary.src.utils.argument_parser as argument_parser

print("before get_args")
args = argument_parser.get_args()
print("after get_args")

SCAN = args.scan
ANALYSE = args.analyse
NUM_BROWSERS = args.num_browsers or 5
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
    # browser_param.profile_archive_dir = Path("./datadir/")

# Update TaskManager configuration (use this for crawl-wide settings)
manager_params.data_directory = Path("./datadir/")
manager_params.log_path = Path("./datadir/openwpm.log")
manager_params.failure_limit = 10000000000000
# memory_watchdog and process_watchdog are useful for large scale cloud crawls.
# Please refer to docs/Configuration.md#platform-configuration-options for more information
# manager_params.memory_watchdog = True
# manager_params.process_watchdog = True

CANARY_BASE_PATH = "./canary/"
SITEMAP_FOLDER_PATH = CANARY_BASE_PATH + "sitemaps/"
FORMS_DB_DIR = "./datadir/forms.sqlite"
conn = lite.connect(FORMS_DB_DIR)
cur = conn.cursor()

error_sites = []
print("before getting site urls")
if args.sitemap_filename:
    sitemap_path = SITEMAP_FOLDER_PATH + args.sitemap_filename
else:
    print("no sitemap param provided, downloading from s3")
    sitemap_path = utils.download_sitemap_from_s3()

site_urls = get_site_urls(page_limit=args.page_limit, sitemap_path = sitemap_path)
print("site urls length : " + str(len(site_urls)))
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
                reset=False
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

epoch_time = int(time.time())
print("error sites")
print(error_sites)

domain_name = site_urls[0].removeprefix("https://").removesuffix("/")
with open('canary/output/error_sites/error_sites_{domain}_{date}.json'.format(domain = domain_name, date = datetime.now().strftime("%m_%d_%Y_%H:%M:%S")), 'w') as outfile:
    json.dump(error_sites, outfile)

if ANALYSE == True:
    print("analysing data")
    if args.pages:
        sites = save_pages(page_limit = args.page_limit, sitemap_path = sitemap_path, domain = domain_name)
    if args.forms:
        print("analysing forms...")
        forms_output = []
        for id, element_id, element_id_type, element_text, element_tag, pages in cur.execute("SELECT * FROM forms;"):
            pagesList = json.loads(pages)
            for page in pagesList:
                formData = {"formID": element_id, "formIDType": element_id_type, "formIDTag": element_tag, "formText": element_text, "dateDetected": epoch_time, "privacyPolicyExists": False, "url": page, "status": "new"}
                forms_output.append(formData)
        conn.close()

        with open('./canary/output/forms/forms_{}.json'.format(epoch_time), 'w') as outfile:
            json.dump(forms_output, outfile)
        print("Dumped forms to file")

    if args.scripts:
        print("analysing scripts...")
        scripts = script_finder.find_scripts()

    if args.all_cookies:
        print("analysing all cookies...")
        all_cookies = all_cookies_finder.find_all_cookies()
        enhanced_cookies, unknown_cookies = cookie_enhancer.get_enhanced_and_unknown_cookies(all_cookies)
        utils.write_json_to_file(unknown_cookies, domain_name, "unknown_cookies", folder="unknown_cookies")

    print("building full payload...")
    with open('canary/templates/payload_empty.json') as f:
        full_site_payload = json.load(f)
        domainData = full_site_payload["domains"][0]
        domainData["domainName"] = domain_name
        if args.pages: 
                domainData["tests"]["changeDetection"]["pages"] = sites
        
        if args.forms:
            domainData["tests"]["changeDetection"]["forms"] = forms_output
        
        if args.scripts:
            domainData["tests"]["changeDetection"]["scripts"] = scripts
        
        if args.all_cookies:
            domainData["tests"]["changeDetection"]["cookies"] = enhanced_cookies
            print("enhanced cookies length: " + str(len(enhanced_cookies)))
                
        file_path = './canary/output/payloads/{domain_name}_{date}.json'.format(domain_name = domainData["domainName"], date = datetime.now().strftime("%m_%d_%Y_%H:%M:%S"))
        with open(file_path, 'w+', encoding='utf-8') as outfile:
                json.dump(full_site_payload, outfile, ensure_ascii=False, indent=4)
                print("Dumped full paylaod to file for: "  + domainData["domainName"])
        print("uploading payload to s3")
        utils.write_payload_to_s3(json.dumps(full_site_payload, ensure_ascii=False, indent=4).encode('UTF-8'), domainData["domainName"])
        # utils.upload_file_to_s3("canary-payloads", file_path, domainData["domainName"] + '.json')