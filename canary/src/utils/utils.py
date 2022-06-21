from datetime import datetime
import json
import os
import boto3
def write_json_to_file(json_obj, domain, file_name, folder = 'files'):
    print(os.getcwd())
    with open('./canary/output/{folder}/{domain}_{date}_{file_name}.json'.format(domain = domain, date = datetime.now().strftime("%m_%d_%Y_%H:%M:%S"), file_name=file_name, folder=folder), 'w+', encoding='utf-8') as outfile:
                json.dump(json_obj, outfile, ensure_ascii=False, indent=4)
                print("Dumped a file for: "  + domain)

def get_sitemap_string_from_s3():
    BUCKET_NAME_STRING = "canary-sitemaps"
    sitemap_s3_filename = os.environ.get('SITEMAP_S3_FILE_NAME')
    s3_client = boto3.client('s3')
    s3_response_object = s3_client.get_object(Bucket=BUCKET_NAME_STRING, Key=sitemap_s3_filename, ResponseContentEncoding='string')
    object_content = s3_response_object['Body'].read().decode('utf-8')
    return object_content

def download_sitemap_from_s3():
    BUCKET_NAME_STRING = "canary-sitemaps"
    sitemap_s3_filename = os.environ.get('SITEMAP_S3_FILE_NAME')
    print("sitemap_s3_filename: " + sitemap_s3_filename)
    s3_client = boto3.client('s3')
    filename = "./canary/sitemaps/" + sitemap_s3_filename
    s3_client.download_file(BUCKET_NAME_STRING, sitemap_s3_filename, filename)
    return filename
    # object_content = s3_response_object['Body'].read().decode('utf-8')
    # return object_content

# download_sitemap_from_s3()
# get_sitemap_string_from_s3()