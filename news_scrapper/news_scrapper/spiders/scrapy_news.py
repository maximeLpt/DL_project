import scrapy
from datetime import datetime
from unicodedata import normalize


class LesEchosSpider(scrapy.Spider):
    name = "les-echos"
    rotate_user_agent = True
    start_urls = [
        'https://www.lesechos.fr',
    ]
    pageCount = 200

    date_mapping = {
        "janv.": 1,
        "févr.": 2,
        "mars": 3,
        "avr.": 4,
        "mai": 5,
        "juin": 6,
        "juil.": 7,
        "août": 8,
        "sept.": 9,
        "oct.": 10,
        "nov.": 11,
        "déc.": 12
    }

    def parse(self, response):
        # get all links linking to tag except the first (a la une)
        links = response.xpath("(//nav)[1]//a/@href").getall()[1:-1]
        # follow every principal tag
        for pageNumber in range(1, self.pageCount+1):
            paged_links = [f'{l}?page={pageNumber}' for l in links]
            for link in paged_links:
                yield response.follow(link, callback=self.parse_principal_tag)

    def parse_principal_tag(self, response):
        # get all links of articles on the page
        links = response.xpath(
            "//article//div/preceding-sibling::a[not(contains(.,'Sélection abonnés'))]/@href"
        ).getall()
        # parse every article from it
        for link in links:
            yield response.follow(link, callback=self.parse_article)

    def decode_utf(self, text):
        return text.encode().decode() if text else None

    def process_content(self, content):
        return normalize("NFKD", "".join(content)) if content else None

    def parse_article(self, response):
        title = self.decode_utf(response.xpath("//header/h1/text()").get())

        _, _, _, *tags, _ = response.url.split("/")
        tags = [self.decode_utf(tag) for tag in tags]

        description = self.decode_utf(
            response.xpath("//header/p/text()").get()
        )

        date_tokens = self.decode_utf(
            response.xpath("//span[contains(.,'Publié')]/text()").get()
        )
        date_tokens = date_tokens.split(" ") if date_tokens else None
        date = None
        if date_tokens:
            _, _, day, month, year, *_ = date_tokens
            date = datetime(int(year), self.date_mapping[month], int(day))

        content = response.xpath(
            "//div[@data-testid='post-description']//*[self::h3 or self::p]/text()").getall()
        content = self.process_content(content)

        yield {
            "title": title,
            "tags": tags,
            "description": description,
            "date": date,
            "content": content,
            "url": response.url
        }


class LiberationSpider(scrapy.Spider):
    name = "liberation"
    rotate_user_agent = True
    start_urls = [
        'https://www.liberation.fr',
    ]
    date_mapping = {
        "janvier": 1,
        "février": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "août": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "décembre": 12
    }

    def parse(self, response):
        # get all links linking to tag except the checknews and portraits
        links = [f'/archives/{year}/' for year in range(2021, 1997, -1)]
        # follow every year
        for link in links:
            yield response.follow(link, callback=self.parse_year)

    def parse_year(self, response):
        # get all links of month and year on the page
        yield from response.follow_all(
            css=".font_xs.color_black.margin-xxs-bottom.decoration_none.width_fit-content",
            callback=self.parse_month
        )

    def parse_month(self, response):
        yield from response.follow_all(
            css=".font_xs.color_black.margin-xxs-bottom.decoration_none.width_fit-content",
            callback=self.parse_day
        )

    def parse_day(self, response):
        # links that are not for abonnées and not tribunes
        links = response.xpath(
            "//article[not(.//span) and not(.//div[@class='font_black font_xs decoration_underline font_tertiary padding-xs-bottom'])]//a/@href"
        )
        for link in links:
            yield response.follow(link, callback=self.parse_article)

    def decode_utf(self, text):
        return text.encode().decode() if text else None

    def process_content(self, content):
        return normalize("NFKD", "".join(content)) if content else None

    def parse_article(self, response):
        title = self.decode_utf(response.xpath("//h1/text()").get())

        tags_links = response.xpath(
            "//a[@class='color_grey hover_underline']/@href").getall()
        tags = tags_links[-1][1:-1].split("/") if tags_links else None
        tags = [self.decode_utf(tag) for tag in tags]

        description = self.decode_utf(
            response.xpath(
                "//span[@class='font_md font_secondary font_line-height_lg display_block']/text()").get()
        )

        date_tokens = self.decode_utf(
            response.xpath(
                "//div[@class='font_xs color_grey margin-xxs-right font_tertiary']/text()").get()
        )
        date_tokens = date_tokens.split(" ") if date_tokens else None
        date = None
        if date_tokens:
            _, _, day, month, year, *_ = date_tokens
            if day == "1er":
                day = "1"
            date = datetime(int(year), self.date_mapping[month], int(day))

        content = response.xpath(
            "//article[contains(@class, 'article-body-wrapper')]/*[not(self::script)]//text()").getall()
        content = self.process_content(content)

        yield {
            "title": title,
            "tags": tags,
            "description": description,
            "date": date,
            "content": content,
            "url": response.url
        }
