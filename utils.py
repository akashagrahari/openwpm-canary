from datetime import datetime
import json

def write_json_to_file(json_obj, domain, file_name):
    with open('{domain}_{date}_{file_name}.json'.format(domain = domain, date = datetime.now().strftime("%m_%d_%Y_%H:%M:%S"), file_name=file_name), 'w+', encoding='utf-8') as outfile:
                json.dump(json_obj, outfile, ensure_ascii=False, indent=4)
                print("Dumped a file for: "  + domain)