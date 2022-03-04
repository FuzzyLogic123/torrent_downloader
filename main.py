import json
import math
import os
from time import sleep

import psutil
from rich import box
from rich.prompt import Confirm
from rich.table import Table
from scrapy.crawler import CrawlerProcess
from transmission_rpc import Client

from web_scraper import Spider_1337x, Spider_thepiratebay, console


def main():
    process = CrawlerProcess(settings={
        "FEEDS": {
            "torrent_items.jsonl": {"format": "jsonlines"},
        },
        "LOG_LEVEL": "ERROR"
    })

    with console.status("Getting torrents...", spinner="monkey"):
        process.crawl(Spider_thepiratebay)
        process.crawl(Spider_1337x)

        process.start()  # the script will block here until the crawling is finished

    # sort torrents
    filesize = os.path.getsize("torrent_items.jsonl")
    if filesize == 0:
        console.print("[red]Sorry no results were returned")
        quit()

    with open('torrent_items.jsonl') as f:
        data = [json.loads(line) for line in f]

    sorted_torrents = sorted(data, key=lambda torrent: int(
        torrent["seeds"]), reverse=True)

    # display torrents to user

    def convert_size(size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s %s" % (s, size_name[i])

    def print_table(sorted_torrents, result_count=20):
        table = Table(title="Available Torrents :popcorn: :movie_camera:",
                      box=box.HEAVY_EDGE, leading=True)

        table.add_column("#", style="yellow bold", no_wrap=True)
        table.add_column("Title", style="cyan")
        table.add_column("Website", style="orange1", no_wrap=True)
        table.add_column("Seeders", style="green", no_wrap=True)
        table.add_column("Size", style="red bold", no_wrap=True)

        for i, torrent in enumerate(sorted_torrents[:result_count]):
            torrent_size = convert_size(
                int(torrent["size"])) if torrent["website"] != "1337x.to" else torrent["size"]
            table.add_row(str(
                i + 1), torrent["name"], torrent["website"], str(torrent["seeds"]), torrent_size)

        console.print(table)

    torrent_count = 10
    torrent_count_delta = torrent_count
    print_table(sorted_torrents, torrent_count)

    user_index_choice = ''
    while not isinstance(user_index_choice, int) or (user_index_choice > torrent_count or user_index_choice < 0):
        console.print(">> ", end='')
        user_index_choice = input('')
        if user_index_choice == '':
            torrent_count += torrent_count_delta
            print_table(sorted_torrents, torrent_count)
        elif user_index_choice == 'quit':
            quit()
        else:
            try:
                user_index_choice = int(user_index_choice)
            except:
                console.print(":warning:[red]Please enter an integer[/]")

    # activate torrent through transmission client

    # for process in psutil.process_iter():
    #     print(process.name)
    # check if transmission-daemon is already running
    if "transmission-daemon" not in (p.name() for p in psutil.process_iter()):
        os.system('transmission-daemon')

    # warn the user they are not connected to vpn
    if "NordVPN" not in (p.name() for p in psutil.process_iter()):
        console.print("[yellow]:warning: You are not connected to a VPN")
        use_vpn = Confirm.ask("Would you like to open NordVPN?")
        if use_vpn:
            os.system("open /Applications/NordVPN.app")
            start_torrent = input('Press enter to start')
            while start_torrent != '':
                start_torrent = input()
    torrent_url = sorted_torrents[user_index_choice - 1]["magnet_url"]

    with console.status("[yellow blink]Connecting client...[/]", spinner="aesthetic"):
        client_launced = False
        while client_launced == False:
            try:
                c = Client(host="localhost", username="admin",
                           password="password", port=9091)
                client_launced = True
            except:
                sleep(0.1)

    c.add_torrent(
        torrent_url, download_dir='/Users/patrickedwards/Desktop/movies and tv.nosync')

    console.print("\n:thumbs_up: [sea_green2]Download Started![/]\n")
    console.print(
        "View Status at [link]http://localhost:9091/transmission/web/\n")


if __name__ == "__main__":
    main()
