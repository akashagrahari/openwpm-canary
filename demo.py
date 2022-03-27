from pathlib import Path

from custom_command import FormCountingCommand, LinkCountingCommand
from openwpm.command_sequence import CommandSequence
from openwpm.commands.browser_commands import GetCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.task_manager import TaskManager
from sites import Sites
import xmltodict
# The list of sites that we wish to crawl
NUM_BROWSERS = 10
SITES_XML_PATH = "sitemap.xml" 

def get_sites():
    pages = []
    with open(SITES_XML_PATH) as xml_file:
        data_dict = xmltodict.parse(xml_file.read())
        urls = data_dict['urlset']['url']
        for url in urls:
            pages.append(url['loc'])
    return pages

sites = get_sites(SITES_XML_PATH)
print(sites)
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


# Commands time out by default after 60 seconds
with TaskManager(
    manager_params,
    browser_params,
    SQLiteStorageProvider(Path("./datadir/crawl-data.sqlite")),
    None,
) as manager:
    # Visits the sites
    for index, site in enumerate(sites):

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
        command_sequence.append_command(FormCountingCommand())

        # Run commands across all browsers (simple parallelization)
        manager.execute_command_sequence(command_sequence)


