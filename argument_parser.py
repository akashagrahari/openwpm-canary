import argparse
import string
def get_args():
    parser = argparse.ArgumentParser(description='Scan and analyse')
    parser.add_argument('--scan', type=bool, required=True, help='scan the provided urls', action=argparse.BooleanOptionalAction)
    parser.add_argument('--analyse', type=bool, required=True, help='analyse the results and save to file', action=argparse.BooleanOptionalAction)
    parser.add_argument('--pages', type=bool, required=True, help='fetch pages from urls', action=argparse.BooleanOptionalAction)
    parser.add_argument('--forms', type=bool, required=True, help='fetch forms from urls', action=argparse.BooleanOptionalAction)
    parser.add_argument('--scripts', type=bool, required=True, help='fetch scripts from urls', action=argparse.BooleanOptionalAction)
    parser.add_argument('--all_cookies', type=bool, required=True, help='fetch all cookies from urls', action=argparse.BooleanOptionalAction)
    parser.add_argument('--allow_ot_cookies', type=bool, required=True, help='Allow cookies for OneTrust banners', action=argparse.BooleanOptionalAction)
    parser.add_argument('--page_limit', type=int, required=False, help='Scanned pages limit')
    parser.add_argument('--sitemap_filename', required=False, help='Sitemap filename')
    args = parser.parse_args()

    print("SCAN = " + str(args.scan))
    print("ANALYSE = " + str(args.analyse))
    print("pages = " + str(args.pages))
    print("forms = " + str(args.forms))
    print("scripts = " + str(args.scripts))
    print("all_cookies = " + str(args.all_cookies))
    print("allow_ot_cookies = " + str(args.allow_ot_cookies))
    print("page_limit = " + str(args.page_limit))
    print("sitemap_filename = " + str(args.sitemap_filename))
    
    return args