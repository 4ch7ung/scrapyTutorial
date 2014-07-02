from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy.item import Item, Field

class categoryItem(Item):
	name = Field()
	pages = Field()
	url = Field()
	url_strip = Field()

class albumsItem(Item):
	albums = Field()

class VukuSpider(Spider):
	"""Spider for porn site http://vuku.ru. Extracts images"""
	name = "vuku"
	base_url = "http://vuku.tv"
	allowed_domains = ["vuku.tv"]
	start_urls = [
		"http://vuku.tv/pornophoto/index.html"
		]

	def make_page_url(self, category):
		"""Creates url ready to include pages and returns it"""
		url_list = self.start_urls[0].split('/')
		url_list.insert(-1, category)
		url_list.insert(-1, "page-%d")
		url = ""
		for url_part in url_list:
			url += url_part + "/"
		return url[:-1]

	def make_page_url_strip(self, category):
		"""Creates strip url for category and returns it"""
		url_list = self.start_urls[0].split('/')
		url_list.insert(-1, category)
		url = ""
		for url_part in url_list:
			url += url_part + "/"
		return url[:-1]
			
	def get_photo_categories(self, response):
		"""Retrieves all photo categories available"""
		sel = Selector(response)
		menu = sel.xpath('//div[@id="photoMenu"]')
		menu_item_links = menu.xpath('.//td[@class="menuItem"]/a/@href').extract()
		categories = []
		for link in menu_item_links:
			category = link.split('/')[-2]
			categories.append(category)
		return categories
	
	def parse(self, response):
		cat_names = self.get_photo_categories(response)
		for cat in (cat_names[0],):
			category = categoryItem()
			category['url'] = self.make_page_url(cat)
			category['url_strip'] = self.make_page_url_strip(cat)
			category['name'] = cat
			req = Request(category['url_strip'], callback=self.dig_deeper, meta={'item':category})
			yield req
#		for cat in cat_names:
				
	def dig_deeper(self, response):
		"""Iterates through all pages in category"""
		category = response.meta['item']
		sel = Selector(response)
		#<li class="last"><a href="*">
		last_adr = sel.xpath('//li[@class="last"]/a/@href').extract()[-1]
		#/pornophoto/devushki/page-*/index.html
		last_page = last_adr.split('/')[-2].split('-')[-1]
		category['pages'] = int(last_page)
		for i in range(1, category['pages']):
			request = Request(category['url'] % i, callback=self.dig_deeper2, meta={'category':category})
			yield request
 		
	def dig_deeper2(self, response):
		sel = Selector(response)
		albums = albumsItem()
		albums['albums'] = []
		album_links = sel.xpath('//span[@class="photoTitle"]/a')
		for link in album_links:
			album = {}
			album['url'] = self.base_url + link.xpath('@href').extract()[0]
			album['title'] = link.xpath('text()').extract()[0]
			albums['albums'].append(album)
