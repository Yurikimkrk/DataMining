import scrapy

from gb_parse.loaders import HHLoader
from gb_parse.spiders.xpaths import HH_PAGE_XPATH, HH_VACANCY_XPATH, \
    HH_COMPANY_XPATH


class HhSpider(scrapy.Spider):
    name = "hh"
    allowed_domains = ["hh.ru"]
    start_urls = [
        "https://krasnoyarsk.hh.ru/search/vacancy?L_is_autosearch=false&L_profession_id=0&area=151"
    ]

    def parse(self, response, **kwargs):
        pagination_list = response.xpath(HH_PAGE_XPATH['pagination'])
        for pag in pagination_list:
            yield response.follow(pag, callback=self.parse)
        vacancy_list = response.xpath(HH_PAGE_XPATH['vacancy'])
        for vacancy in vacancy_list:
            yield response.follow(vacancy, callback=self.vacancy_parse)

    def vacancy_parse(self, response):
        loader = HHLoader(response=response)
        loader.add_value('url', response.url)
        for key, value in HH_VACANCY_XPATH.items():
            loader.add_xpath(key, value)
        yield loader.load_item()
        yield response.follow(
            response.xpath(HH_VACANCY_XPATH["company_url"]).get(),
            callback=self.company_parse
        )

    def company_parse(self, response):
        loader = HHLoader(response=response)
        for key, value in HH_COMPANY_XPATH.items():
            loader.add_xpath(key, value)
        yield loader.load_item()