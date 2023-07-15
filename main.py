import feedparser
from html.parser import HTMLParser
from collections import defaultdict
import requests
from bs4 import BeautifulSoup
import edge_tts
import asyncio
from pydub import AudioSegment
from pydub.playback import play
from alive_progress import alive_bar
from progress.spinner import MoonSpinner
import time

rss_url = list(map(str, input('Enter any number of RSS feeds you want separated by a space: ').split()))


text_to_read = ""

class MyHTMLParser(HTMLParser):
    def __init__(self):
        self.count = defaultdict(int)
        super().__init__()

    def handle_starttag(self, tag, attrs):
        self.count[tag] += 1

    def handle_startendtag(self, tag, attrs):
        self.count[tag] += 1

def count_tags(html):
    parser = MyHTMLParser()
    parser.feed(html)
    return parser.count

def run_parser():
    global text_to_read
    try:
        for y in range(len(rss_url)):
            d = feedparser.parse(rss_url[y])
            response = requests.get(rss_url[y])
            soup = BeautifulSoup(response.text, 'xml')
            html = str(soup)
            tags = count_tags(html)
            number_of_items = tags['item']
            print(' Fetching data... ')
                   # default setting
            with alive_bar(number_of_items) as bar:
                for x in range(number_of_items):
                    bar()
                    #print(d.entries[x].title)
                    #print(d.entries[x].description)
                    #print(d.entries[x].link+'\n')
                    text_to_read += d.entries[x].title
                    text_to_read += '\n'
                    text_to_read += d.entries[x].description
                    text_to_read += '\n'

    except Exception as e:
        print(text_to_read)
        print('An exception occurred, unable to fetch feed: {e}' )



voice = "en-GB-SoniaNeural"
output_audio_file = 'audio.mp3'

async def amain() -> None:
    """Main function"""
    communicate = edge_tts.Communicate(text_to_read, voice)
    submaker = edge_tts.SubMaker()
    with open(output_audio_file, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])


if __name__ == "__main__":
    run_parser()
    loop = asyncio.get_event_loop_policy().get_event_loop()
    with MoonSpinner(' Generating audio, please wait... ') as bar:
        for i in range(100):
            time.sleep(0.02)
            bar.next()
    try:
        loop.run_until_complete(amain())
    finally:
        loop.close()
        song = AudioSegment.from_mp3("audio.mp3")
        print(' Playing news on default audio device... ')
        play(song)
