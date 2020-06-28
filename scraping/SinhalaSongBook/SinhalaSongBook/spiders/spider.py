import scrapy
import requests
from scrapy.spiders import SitemapSpider
from scrapy.http.request import Request
from SinhalaSongBook.items import SinhalaSongBookItem
import re
import os

class SinhalaSongBookSpider(scrapy.Spider):
    name = "SinhalaSongBook"
    start_urls   = ["https://sinhalasongbook.com/all-sinhala-song-lyrics-and-chords/?_page="+ str(i) for i in range(1, 22)]
    n_pages = 21
    song_count = 0

    def parse_song(self, response):
        song = SinhalaSongBookItem()
        song['title_en'] = response.xpath('//div[@class="entry-content"]/h2/text()').get()
        song['title_si'] = response.xpath('//span[@class="sinTitle"]/text()').get()
        song['artist'] = response.xpath('//div[@class="su-row"]//span[@class="entry-categories"]//a/text()').extract()
        song['genre'] = response.xpath('//div[@class="su-row"]//span[@class="entry-tags"]//a/text()').extract()        
        song['writer'] = response.xpath('//div[@class="su-row"]//span[@class="lyrics"]//a/text()').extract()        
        song['composer']  = response.xpath('//div[@class="su-row"]//span[@class="music"]//a/text()').extract()
        n_visits = response.xpath('//div[@class="tptn_counter"]/text()').extract()
        n_visits_digits = [word for word in str(n_visits) if word.isdigit()]
        song['n_visits'] = int(''.join(n_visits_digits))

        songBody = response.xpath('//div[@class="entry-content"]//pre/text()').extract()
        songBodySplit = []
        for parts in songBody:
            lines = parts.split('\n')
            for line in lines:
                songBodySplit.append(line)
        
        lyrics = ""

        for line in songBodySplit:
            if(not(re.search('[a-zA-Z]', line))):
                if(len(line)!=0):
                    line = line.replace('+','')
                    line = line.replace('|','')
                    line.strip()
                    lyrics = lyrics + line + os.linesep
                
        song['lyrics'] = lyrics
        
        yield song
        

    def parse(self, response):
        for href in response.xpath('//div[@class="col-md-6 col-sm-6 col-xs-12 pt-cv-content-item pt-cv-1-col"]//a/@href'):
            self.song_count = self.song_count + 1
            yield scrapy.Request(href.extract(), callback=self.parse_song)