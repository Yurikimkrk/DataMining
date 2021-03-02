import scrapy
import pymongo
import re


class AutoyoulaSpider(scrapy.Spider):
    name = "autoyoula"
    allowed_domains = ["auto.youla.ru"]
    start_urls = ["https://auto.youla.ru/"]

    _css_selectors = {
        "brands": ".TransportMainFilters_brandsList__2tIkv "
                  ".ColumnItemList_container__5gTrc "
                  "a.blackLink",
        "pagination": "a.Paginator_button__u1e7D",
        "car": ".SerpSnippet_titleWrapper__38bZM a.SerpSnippet_name__3F7Yu",
    }
    data_query = {
        "title": lambda resp: resp.css(
            "div.AdvertCard_advertTitle__1S1Ak::text").get(),
        "price": lambda resp: float(
            resp.css("div.AdvertCard_price__3dDCr::text").get().replace("\u2009", "")
        ),
        "photos": lambda resp: [
            i.attrib.get("src") for i in
            resp.css("figure.PhotoGallery_photo__36e_r img")
        ],
        "characteristics": lambda resp: [
            {
                "name": i.css(
                    ".AdvertSpecs_label__2JHnS::text").extract_first(),
                "value": i.css(
                    ".AdvertSpecs_data__xK2Qx::text").extract_first()
                         or i.css(
                    ".AdvertSpecs_data__xK2Qx a::text").extract_first(),
            }
            for i in
            resp.css("div.AdvertCard_specs__2FEHc .AdvertSpecs_row__ljPcX")
        ],
        "descript": lambda resp: resp.css(
            ".AdvertCard_descriptionInner__KnuRi::text"
        ).extract_first(),
        "author": lambda resp: AutoyoulaSpider.get_author_id(resp),
    }

    @staticmethod
    def get_author_id(resp):
        marker = "window.transitState = decodeURIComponent"
        for script in resp.css("script"):
            try:
                if marker in script.css("::text").extract_first():
                    re_pattern = re.compile(
                        r"youlaId%22%2C%22([a-zA-Z|\d]+)%22%2C%22avatar")
                    result = re.findall(re_pattern,
                                        script.css("::text").extract_first())
                    return f"https://youla.ru/user/{result[0]}" if result else None
            except TypeError:
                pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_client = pymongo.MongoClient("mongodb://localhost:27017")

    def _get_follow(self, response, select_str, callback, **kwargs):
        for a in response.css(select_str):
            link = a.attrib.get("href")
            yield response.follow(link, callback=callback, cb_kwargs=kwargs)

    def parse(self, response, *args, **kwargs):
        yield from self._get_follow(
            response, self._css_selectors["brands"], self.brand_parse,
            hello="moto"
        )

    def brand_parse(self, response, **kwargs):
        yield from self._get_follow(
            response, self._css_selectors["pagination"], self.brand_parse,
        )
        yield from self._get_follow(response, self._css_selectors["car"],
                                    self.car_parse)

    def car_parse(self, response):
        data = {}
        for key, selector in self.data_query.items():
            try:
                data[key] = selector(response)
            except:
                continue
        self.db_client["DataMiningYoula"][self.name].insert_one(data)
