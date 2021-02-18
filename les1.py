from pathlib import Path
import requests
import time
import json


class Parse5ka:
    # add params for categories
    params = {}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) '
                      'Gecko/20100101 Firefox/85.0'}

    def __init__(self, start_url: str, save_path: Path):
        self.start_url = start_url
        self.save_path = save_path

    def _get_response(self, url):
        while True:
            response = requests.get(url, params=self.params,
                                    headers=self.headers)
            if response.status_code == 200:
                return response
            time.sleep(0.5)

    def run(self):
        for product in self._parse(self.start_url):
            product_path = self.save_path.joinpath(f'{product["id"]}.json')
            self._save(product, product_path)

    def _parse(self, url: str):
        while url:
            data = (self._get_response(url)).json()
            url = data['next']
            for product in data['results']:
                yield product

    def _save(self, data: dict, file_path: Path):
        file_path.write_text(json.dumps(data, ensure_ascii=False))


# inherited from the main parser and add categories url
class ParseCategories(Parse5ka):
    def __init__(self, categories_url, start_url, save_path):
        super().__init__(start_url, save_path)
        self.categories_url = categories_url

    def _get_categories(self, url):
        response = (self._get_response(url)).json()
        return response

    def run(self):
        for category in self._get_categories(self.categories_url):
            # add categories in params to filter by them
            self.params["categories"] = category["parent_group_code"]
            category["products"] = list(self._parse(self.start_url))
            # create files by category name (it's bad practice to write the
            # names of files in cyrillic, but it's more visually if you
            # collect data for yourself)
            file_path = self.save_path.joinpath(
                f'{category["parent_group_name"]}.json')
            # check the category before creating the file
            # (filter out the categories without products)
            if category["products"] != []:
                self._save(category, file_path)


if __name__ == '__main__':
    offers_url = "https://5ka.ru/api/v2/special_offers/"
    # add url with sale categories
    categories_url = "https://5ka.ru/api/v2/categories/"
    save_path = Path(__file__).parent.joinpath("promotions")
    if not save_path.exists():
        save_path.mkdir()
    parser = ParseCategories(categories_url, offers_url, save_path)
    parser.run()
