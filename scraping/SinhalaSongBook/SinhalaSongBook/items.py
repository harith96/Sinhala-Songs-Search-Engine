# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SinhalaSongBookItem(scrapy.Item):
    title_en = scrapy.Field()
    title_si = scrapy.Field() 
    artist = scrapy.Field() 
    genre = scrapy.Field() 
    writer = scrapy.Field() 
    composer = scrapy.Field() 
    n_visits = scrapy.Field() 
    lyrics = scrapy.Field() 
    pass
