import xmltodict

def get_sites(path):
    pages = []
    with open(path) as xml_file:
        data_dict = xmltodict.parse(xml_file.read())
        urls = data_dict['urlset']['url']
        for url in urls:
            pages.append(dict(url = url['loc'], dateDetected = int(time.time()), status = "new"))
    return pages

