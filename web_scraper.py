import json
import os
import urllib.parse
import psutil

import scrapy
from rich.console import Console
from rich.prompt import Confirm
from rich.traceback import install

#init rich
install()
console = Console()


def check_for_vpn():
    # warn the user they are not connected to vpn
    if "NordVPN" not in (p.name() for p in psutil.process_iter()):
        console.print("[yellow]:warning: You are not connected to a VPN")
        use_vpn = Confirm.ask("Would you like to open NordVPN?")
        if use_vpn:
            os.system("open /Applications/NordVPN.app")
            start_torrent = input('')
            while start_torrent != '':
                start_torrent = input()


#get torrent data
os.path.exists("torrent_items.jsonl") and os.remove("torrent_items.jsonl")

check_for_vpn()
console.print(":popcorn:")
search_query = input('')
# search_query = 'euphoria s02e04'
# search_query = 'harry potter'

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
        if data[0]["name"] != "No results returned":
            for i in range(len(data)):
                current_item = data[i]
                current_item["website"] = "thepiratebay.org"
                current_item["seeds"] = current_item.pop("seeders", 0)

                current_item["torrent_page_link"] = f'https://thepiratebay.org/description.php?id={current_item["id"]}]'
                current_item["magnet_url"] = f"magnet:?xt=urn:btih:{current_item['info_hash']}&dn={urllib.parse.quote(current_item['name'])}"
                yield current_item
