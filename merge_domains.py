from sys import argv
from datetime import datetime
import json
domain_files = argv[1:]
# domain_files = ["www.arstechnica.com_05_16_2022_11:44:02.json", "www.glamour.de_05_15_2022_17:54:37.json"]
print(domain_files)
with open('payload_template.json') as f:
        full_site_payload = json.load(f)
        for domain_file in domain_files:
            with open(domain_file) as df:
                domain_payload = json.load(df)
                domain_data = domain_payload["domains"][0]
                full_site_payload["domains"].append(domain_data)

with open('merged_domains_{date}.json'.format(date = datetime.now().strftime("%m_%d_%Y_%H:%M:%S")), 'w+', encoding='utf-8') as outfile:
                json.dump(full_site_payload, outfile, ensure_ascii=False, indent=4)
                print("Dumped full paylaod to file")