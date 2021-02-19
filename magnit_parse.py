from urllib.parse import urljoin
import requests
import bs4
import pymongo
from datetime import datetime

MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


class MagnitParse:
    def __init__(self, start_url, db_client):
        self.start_url = start_url
        self.db = db_client["GB_DataMining"]
        self.collection = self.db["magnit_products"]

    def _get_response(self, url):
        return requests.get(url)

    def _get_soup(self, url):
        response = self._get_response(url)
        return bs4.BeautifulSoup(response.text, "lxml")

    def run(self):
        soup = self._get_soup(self.start_url)
        catalog = soup.find("div", attrs={"class": "сatalogue__main"})
        for prod_a in catalog.find_all("a", recursive=False):
            product_data = self._parse(prod_a)
            self._save(product_data)

    def get_template(self):
        return {
            'url': lambda a: urljoin(self.start_url, a.attrs.get('href')),
            'promo_name': lambda a: a.find('div', attrs={'class':
                                                             'card-sale__header'}).text,
            'product_name': lambda a: a.find('div', attrs={'class':
                                                               'card-sale__title'}).text,
            'old_price': lambda a: float(
                '.'.join(itm for itm in a.find('div', attrs={'class':
                                                                 'label__price_old'}).text.split())),
            'new_price': lambda a: float(
                '.'.join(itm for itm in a.find('div', attrs={'class':
                                                                 'label__price_new'}).text.split())),
            'image_url': lambda a: urljoin(self.start_url, a.find(
                'img').attrs.get('data-src')),
            'date_from': lambda a: self.str_to_datetime((a.find('div', attrs={
                'class': 'card-sale__date'}).text).replace(
                'с ', '').replace('\n', '').split('до ')[0]),
            'date_to': lambda a: self.str_to_datetime((a.find('div', attrs={
                'class': 'card-sale__date'}).text).replace(
                'с ', '').replace('\n', '').split('до ')[1])
        }

    def _parse(self, product_a) -> dict:
        data = {}
        for key, funk in self.get_template().items():
            try:
                data[key] = funk(product_a)
            except:
                continue
        return data

    def _save(self, data: dict):
        self.collection.insert_one(data)

    def str_to_datetime(self, str):
        date = str.split(' ')
        return datetime(year=datetime.now().year, day=int(date[0]),
                        month=MONTHS[date[1]])


if __name__ == "__main__":
    url = "https://magnit.ru/promo/"
    db_client = pymongo.MongoClient("mongodb://localhost:27017")
    parser = MagnitParse(url, db_client)
    parser.run()
