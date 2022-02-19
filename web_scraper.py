import json
import urllib.parse
import requests
import scrapy
from scrapy.crawler import CrawlerProcess
import imdb
import os
import time
from rich.traceback import install
from rich import print
from rich.console import Console
from rich import inspect

console = Console()
install(show_locals=True)

# # #get torrent data
t0 = time.time()
os.path.exists("torrent_items.jsonl") and os.remove("torrent_items.jsonl")

# # search_query = input('What would you like to search for?\n')
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
                "name": row.css('td.name a[href*=torrent]::text').get(),
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
            "magnet_url": response.css('a[href*=magnet]::attr(href)').get()
        }


class Spider_thepiratebay(scrapy.Spider):
    name = "thepiratebay_scraper"
    start_urls = [f"https://apibay.org/q.php?q={search_query}&cat="]

    def parse(self, response):
        data = json.loads(response.text)
        for i in range(len(data)):
            current_item = data[i]
            current_item["website"] = "thepiratebay.org"
            current_item["seeds"] = current_item.pop("seeders", 0)
            current_item["torrent_page_link"] = f'https://thepiratebay.org/description.php?id={current_item["id"]}]'
            current_item["magnet_url"] = f"magnet:?xt=urn:btih:{current_item['info_hash']}&dn={urllib.parse.quote(current_item['name'])}"
            yield current_item


process = CrawlerProcess(settings={
    "FEEDS": {
        "torrent_items.jsonl": {"format": "jsonlines"},
    },
})

process.crawl(Spider_thepiratebay)
process.crawl(Spider_1337x)


process.start() # the script will block here until the crawling is finished


#get imdb id and query EZTV
ia = imdb.Cinemagoer()
search_results = ia.search_movie(search_query)
#display the results to the user so that they can choose the right one...
imdb_id = search_results[0].movieID
print(imdb_id)
request = requests.get(f'https://eztv.re/api/get-torrents?imdb_id={imdb_id}')

with open('torrent_items.jsonl', 'a') as file:
    torrent_data = request.json()
    for torrent in torrent_data["torrents"]:
        torrent["website"] = "EZTV"
        torrent["name"] = torrent.pop("filename", '')
        json.dump(torrent, file)
        file.write('\n')


##sort torrents
with open('torrent_items.jsonl') as f:
    data = [json.loads(line) for line in f]

sorted_torrents = sorted(data, key=lambda torrent: int(torrent["seeds"]), reverse=True)

for name in sorted_torrents[:10]:
    print(f"[yellow]{name['seeds']}[/yellow]", f"[green]{name['website']}[/green]", f"[blue]{name['name']}[/blue]")

#display torrents to user




#activate torrent through transmission client

t1 = time.time()

print(t1 - t0)