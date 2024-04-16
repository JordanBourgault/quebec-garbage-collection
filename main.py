import html_to_json
import locale
from datetime import datetime
import requests
from bs4 import BeautifulSoup


locale.setlocale(locale.LC_ALL, 'fr_CA')
current_month = None
current_year = None
dates = []
session = requests.session()


def get_session_cookies(address):
    url = 'https://www.ville.quebec.qc.ca/services/info-collecte/index.aspx'
    res = session.get(url).text
    parsed_html = BeautifulSoup(res, 'html.parser')
    viewstate = parsed_html.body.find(id = '__VIEWSTATE').get('value')
    viewstategenerator = parsed_html.body.find(id = '__VIEWSTATEGENERATOR').get('value')
    eventvalidation = parsed_html.body.find(id = '__EVENTVALIDATION').get('value')

    form = {
        "ctl00$ctl00$contenu$texte_page$ucInfoCollecteRechercheAdresse$RechercheAdresse$txtNomRue": (None, address),
        "ctl00$ctl00$contenu$texte_page$ucInfoCollecteRechercheAdresse$RechercheAdresse$BtnRue": (None, "Rechercher"),
        "__VIEWSTATE": (None, viewstate),
        "__VIEWSTATEGENERATOR": (None, viewstategenerator),
        "__EVENTVALIDATION": (None, eventvalidation)
	}
    session.post(url, data=form)

def get_trash_data():
    url = 'https://www.ville.quebec.qc.ca/services/info-collecte/afficherResultats.aspx'
    return session.get(url).text

def clean_up_trash_attribute(attributes):
    return [attribute.removesuffix('.png').removeprefix('picto-') for attribute in attributes]

def format_datetime(year, month, day):
    date = '-'.join([year, month, day])
    return datetime.strptime(date, '%Y-%B-%d').strftime('%Y-%m-%d')

def process_dates(object):
    if isinstance(object, dict):
        check_month(object)
        check_date(object)
        for k, v in object.items():
            if isinstance(v, dict):
                check_month(v)
                check_date(v)
                process_dates(v)
            if isinstance(v, list):
                for item in v:
                    process_dates(item)
    if isinstance(object, list):
        for item in object:
            process_dates(item)

def check_date(obj):
    date_value = None
    image_src = []
    for item in obj.get("p", []):
        if not date_value:
            date_value = item.get("_value")
        for image in item.get("img", []):
            image_src.append(image.get("_attributes").get("src", "").split('/')[-1])
    if image_src:
        global current_month, current_year
        dates.append({
            "date": format_datetime(current_year, current_month, date_value),
            "type": clean_up_trash_attribute(image_src)
        })

def check_month(obj):
    if obj.get("caption"):
        global current_month, current_year
        current_month, current_year = obj.get("caption")[0].get("_value").split(" ")

get_session_cookies("393 rue Gingras")
html_data = get_trash_data()
process_dates(html_to_json.convert(html_data))
print(dates)
