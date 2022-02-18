import scrapy
from scrapy.crawler import CrawlerProcess

# search_query = input('What would you like to search for?\n')
search_query = 'euphoria'

class Spider_1337x(scrapy.Spider):
    # Your spider definition
    name = "1337x_scraper"
    start_urls = [f"https://1337x.to/search/{search_query}/1/"]

    def parse(self, response):
        for row in response.css('tbody tr'):
            torrent_link = response.urljoin(row.css('td.name a[href*=torrent]::attr(href)').get())
            torrent_info =  {
                "website": "1337x.to",
                "torrent_title": row.css('td.name a[href*=torrent]::text').get(),
                "torrent_page_link": torrent_link,
                "seeds": row.css('td.seeds::text').get(),
                "leeches": row.css('td.leeches::text').get(),
                "upload_date": row.css('td.coll-date::text').get(),
                "size": row.css('td.size::text').get(),
                "uploader": row.css('td.uploader a::text').get() or row.css('td.vip a::text').get()
            }
            if torrent_link is not None:
                yield response.follow(torrent_link, callback=self.parse_magnet_link, meta = {"torrent_info": torrent_info})
    def parse_magnet_link(self, response):
        torrent_info = response.meta["torrent_info"]
        yield torrent_info | {
            "magnet_link": response.css('a[href*=magnet]::attr(href)').get()
        }


process = CrawlerProcess(settings={
    "FEEDS": {
        "torrent_items.json": {"format": "json", "overwrite": True},
    },
})

process.crawl(Spider_1337x)
process.start() # the script will block here until the crawling is finished