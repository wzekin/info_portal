import scrapy
from bupt_portal.items import BuptPortalItem
from scrapy.http import FormRequest
from scrapy.http.request import Request
from scrapy.http.response import Response


class NoticeSpider(scrapy.Spider):
    name = "notice"
    user_agent = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
    base_url = "http://my.bupt.edu.cn/"
    allowed_domains = ["my.bupt.edu.cn", "auth.bupt.edu.cn"]
    start_urls = [
        "http://auth.bupt.edu.cn/authserver/login?service=http://my.bupt.edu.cn/"
    ]

    def parse(self, response):
        token = response.xpath('//*[@name="lt"]/@value').extract_first()
        return FormRequest.from_response(
            response,
            formdata={
                "lt": token,
                "execution": "e1s1",
                "_eventId": "submit",
                "rmShown": "1",
                "password": self.settings.get("BUPT_PASSWORD"),
                "username": self.settings.get("BUPT_USERNAME"),
            },
            callback=self.js_redirect,
        )

    def js_redirect(self, response):
        return Request(
            "http://my.bupt.edu.cn/list.jsp?PAGENUM=%s&wbtreeid=1154",
            callback=self.scrape_pages,
        )

    def scrape_pages(self, response: Response):
        for i in range(1, 100):
            yield Request(
                "http://my.bupt.edu.cn/list.jsp?PAGENUM=%s&wbtreeid=1154" % i,
                callback=self.scrape_page,
            )

    def scrape_page(self, response: Response):
        l = response.css(
            "body > div.wbox.mainbox.clearfix > div > div.main.pull-right > ul > li > a::attr(href)"
        )
        for a in l:
            yield Request(self.base_url + a.extract(), callback=self.scrape_content)

    def scrape_content(self, response: Response):
        title = response.css("title::text").get()
        url = response.url
        content_list = response.css(
            "body > div.wbox.mainbox.clearfix > div.singleinner.clearfix > div.singlemainbox.pull-left > form > div:nth-child(2) ::text"
        ).extract()
        new_content = []
        for c in content_list:
            if c.strip() != "":
                new_content.append(c)
        content = "\n".join(new_content)
        yield BuptPortalItem(title=title, url=url, content=content)
