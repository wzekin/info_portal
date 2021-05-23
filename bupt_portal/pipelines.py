# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sqlite3


class BuptPortalPipeline:
    def process_item(self, item, spider):
        return item


class Sqlite3Pipeline(object):

    def __init__(self, sqlite_file, sqlite_table):
        self.sqlite_file = sqlite_file
        self.sqlite_table = sqlite_table

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            sqlite_file=crawler.settings.get(
                'SQLITE_FILE'),  # 从 settings.py 提取
            sqlite_table=crawler.settings.get('SQLITE_TABLE', 'items')
        )

    def open_spider(self, spider):
        self.conn = sqlite3.connect(self.sqlite_file)
        self.cur = self.conn.cursor()
        self.cur.execute("""
            create table if not exists {0}(
                `title` varchar(50),
                `url` varchar(255) UNIQUE,
                `content` text
            )
            """.format(self.sqlite_table))
        self.conn.commit()

    def close_spider(self, spider):
        self.conn.close()

    def process_item(self, item, spider):
        insert_sql = "insert into {0}({1}) values ({2})".format(self.sqlite_table,
                                                                ', '.join(
                                                                    item.keys()),
                                                                ', '.join(['?'] * len(item.keys())))
        self.cur.execute(insert_sql, list(map(lambda x:x[1],item.items())))
        self.conn.commit()

        return item
