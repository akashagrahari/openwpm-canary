from sys import argv
from datetime import datetime
import json
import requests
import utils

file = argv[1]
# file = "www.arstechnica.com_05_16_2022_11:44:02.json"
def get_cookies_from_cookie_API():
    url = "https://data.mongodb-api.com/app/data-iyckn/endpoint/data/beta/action/find"

    payload="{\n    \"collection\": \"cookies\",\n    \"database\": \"cookiesDB\",\n    \"dataSource\": \"DataDrop\"\n}"
    headers = {
    'api-key': '0ce3Durrlxvkc835t2QW9WHfemuor6svhR1hVwX9mDx0PS5qGrbWwcTZz0AUYpLM',
    'Authorization': 'Bearer 0ce3Durrlxvkc835t2QW9WHfemuor6svhR1hVwX9mDx0PS5qGrbWwcTZz0AUYpLM',
    'Content-Type': 'text/plain'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    json_res = json.loads(response.text)["documents"]
    # print(json_res)
    return json_res

def get_wildcard_cookie_by_cookie_name(cookie_name, wildcard_cookies):
    for wildcard_cookie in wildcard_cookies:
        if cookie_name.startswith(wildcard_cookie["name"]):
            return wildcard_cookie
    return None

def get_cookie_by_name_and_domain(cookie_name, cookie_domain, cookie_list):
    for cookie in cookie_list:
        if cookie["name"] == cookie_name and cookie["domain"] == cookie_domain:
            return cookie
    return None

def get_enhanced_cookie(c, cookies_data_array):
    for cookie in cookies_data_array:
        if cookie["name"] == c["name"]: # and cookie["domain"] == c["domain"]
            c.update(cookie)
            return c
    return None

def enhance_cookies_from_file(file_path):
    with open(file_path) as f:
        payload = json.load(f)
        all_cookies = payload["domains"][0]["tests"]["changeDetection"]["cookies"]
        enhanced_cookies, unknown_cookies = get_enhanced_and_unknown_cookies(all_cookies)
    
    payload["domains"][0]["tests"]["changeDetection"]["cookies"] = enhanced_cookies
    utils.write_json_to_file(payload, payload["domains"][0]["domainName"], "enhanced")
    utils.write_json_to_file(unknown_cookies, payload["domains"][0]["domainName"], "unknown_cookies")
    # with open('{domain_name}_{date}_enhanced.json'.format(domain_name = payload["domains"][0]["domainName"], date = datetime.now().strftime("%m_%d_%Y_%H:%M:%S")), 'w+', encoding='utf-8') as outfile:
    #             json.dump(payload, outfile, ensure_ascii=False, indent=4)
    #             print("Dumped paylaod with enhanced cookies to file for: "  + payload["domains"][0]["domainName"])

    # with open('{domain_name}_{date}_unknown_cookies.json'.format(domain_name = , date = datetime.now().strftime("%m_%d_%Y_%H:%M:%S")), 'w+', encoding='utf-8') as outfile:
    #             json.dump(unknown_cookies, outfile, ensure_ascii=False, indent=4)
    #             print("Dumped unknown cookies paylaod to file for: "  + payload["domains"][0]["domainName"])


def get_enhanced_and_unknown_cookies(cookies):
    cookies_data = get_cookies_from_cookie_API()
    enhanced_cookies = []
    unknown_cookies = [] 
    wildcard_cookies = [c for c in cookies_data if c["wildcard match"] == '1']
    for c in cookies:
        enhanced_cookie = get_enhanced_cookie(c, cookies_data)
        if enhanced_cookie != None:
            enhanced_cookies.append(enhanced_cookie)
        else: # not found, check if there's a wildcard cookie that matches
            wildcard_cookie = get_wildcard_cookie_by_cookie_name(c["name"], wildcard_cookies)
            if wildcard_cookie != None: # Found a wildcard cookie for this cookie
                # if wildcard_cookie["wildcard match"] == "1":
                # a wildcard cookie was found
                # check if this wildcard cookie was already added
                enhanced_wildcard_cookie = get_cookie_by_name_and_domain(wildcard_cookie["name"], c["domain"], enhanced_cookies)
                if enhanced_wildcard_cookie != None:
                    # wildcard cookie was already added, append pages to the existing one
                    url_set = set(enhanced_wildcard_cookie["urls"])
                    url_set.update(c["urls"])
                    enhanced_wildcard_cookie["urls"] = list(url_set)
                else:
                    # wildcard cookie was not already added, add it
                    c.update(wildcard_cookie) #TODO: needed?
                    enhanced_cookies.append(c)
                
            else:
                enhanced_cookies.append(c)
                unknown_cookies.append({"name" : c["name"], "domain" : c["domain"]})  # "value" : c["value"]
        # if enhanced_cookie == None and wildcard_cookie == None:
        #     unknown_cookies.append({"name" : c["name"], "domain" : c["domain"]}) #, "value" : c["value"]
        #     enhanced_cookies.append(c) # Adding the unknown cookie anyway 
        # else:
        #     if enhanced_cookie["wildcard match"] == "1":
        #         # wildcard_cookie = get_cookie_by_name_and_domain(enhanced_cookie["name"], enhanced_cookie["domain"], enhanced_cookies)
        #         enhanced_wildcard_cookie = get_cookie_by_name_and_domain(wildcard_cookie["name"], enhanced_cookie["domain"], enhanced_cookies)
        #         if enhanced_wildcard_cookie == None:
        #             enhanced_cookie.update(wildcard_cookie)
        #             enhanced_cookies.append(enhanced_cookie)
        #         else:
        #             enhanced_wildcard_cookie.urls.append(c.urls)
        #         # enhanced_cookies.
        #     else:    
    map(lambda c: c.pop("value"), enhanced_cookies)
    return enhanced_cookies, unknown_cookies


# enhance_cookies_from_file(file)