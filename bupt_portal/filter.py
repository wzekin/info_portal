import logging
import sqlite3

from scrapy.dupefilters import BaseDupeFilter
from scrapy.utils.request import referer_str, request_fingerprint

from bupt_portal.pipelines import Sqlite3Pipeline


class Myfilter(BaseDupeFilter):
    def __init__(self, sqlite_file, sqlite_table, debug=False):
        self.fingerprints = set()
        self.logdupes = True
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        self.sqlite_file = sqlite_file
        self.sqlite_table = sqlite_table

    @classmethod
    def from_settings(cls, settings):
        return cls(
            sqlite_file=settings.get("SQLITE_FILE"),  # 从 settings.py 提取
            sqlite_table=settings.get("SQLITE_TABLE", "items"),
            debug=settings.getbool("DUPEFILTER_DEBUG"),
        )

    def open(self):
        self.conn = sqlite3.connect(self.sqlite_file)
        self.cur = self.conn.cursor()

    def close(self, reason):
        self.conn.close()

    def request_seen(self, request):
        # fp = self.request_fingerprint(request)
        # if fp in self.fingerprints:
        # return True
        # self.fingerprints.add(fp)
        data = self.cur.execute(
            "select url from {0} where url = ?".format(self.sqlite_table), [request.url]
        )
        if len(list(data)) > 0:
            return True
        return False

    def request_fingerprint(self, request):
        return request_fingerprint(request)

    def log(self, request, spider):
        if self.debug:
            msg = "Filtered duplicate request: %(request)s (referer: %(referer)s)"
            args = {"request": request, "referer": referer_str(request)}
            self.logger.debug(msg, args, extra={"spider": spider})
        elif self.logdupes:
            msg = (
                "Filtered duplicate request: %(request)s"
                " - no more duplicates will be shown"
                " (see DUPEFILTER_DEBUG to show all duplicates)"
            )
            self.logger.debug(msg, {"request": request}, extra={"spider": spider})
            self.logdupes = False

        spider.crawler.stats.inc_value("dupefilter/filtered", spider=spider)
