import scrapy
import re

from city_scrapers_core.constants import NOT_CLASSIFIED
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider

from io import BytesIO

from PyPDF2 import PdfFileReader


class IlSexOffenderManagementSpider(CityScrapersSpider):
    name = "il_sex_offender_management"
    agency = "Illinois Sex Offender Management Board"
    timezone = "America/Chicago"
    allowed_domains = ["www2.illinois.gov"]
    start_urls = ["https://www2.illinois.gov/idoc/Pages/SexOffenderManagementBoard.aspx"]

    def __init__(self, *args, **kwargs):
        self.meetings_link = {}
        super().__init__(*args, **kwargs)

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        meeting_link = ""

        for item in response.css(
            ".soi-article-content #ctl00_PlaceHolderMain_ctl01__ControlWrapper_RichHtmlField ul > li"
        ):
            link = item.css("a")
            title = link.css("*::text").get()
            if "Minutes" not in title and "Agenda" not in title:
                continue

            meeting_link = link.attrib["href"]
            self.meetings_link[title] = meeting_link

        if not self.meetings_link:
            raise ValueError("Required links not found")

        yield scrapy.Request(
            response.urljoin(meeting_link), callback=self._parse_meeting, dont_filter=True
        )

    def _parse_meeting(self, response):
        """Parse PDF and yield to documents page"""
        self._parse_meeting_pdf(response)

    def _parse_meeting_pdf(self, response):
        """Parse dates and details from schedule PDF"""
        pdf_obj = PdfFileReader(BytesIO(response.body))
        pdf_text = pdf_obj.getPage(0).extractText()
        # Join lines where there's only a single character, then remove newline
        clean_text = re.sub(r"(?<=[A-Z0-9:])\n", "", pdf_text, flags=re.M).replace("\n", " ")
        # Remove duplicate spaces
        clean_text = re.sub(r"\s+", " ", clean_text)

    def _parse_title(self, item):
        """ Parses the meeting title from the IL Sex Offender Management Board.
        The title can either be "Meeting Minutes" or "Meeting Agenda".
        """
        return ""

    def _parse_description(self, item):
        """Parse or generate meeting description."""
        return ""

    def _parse_classification(self, item):
        """Parse or generate classification from allowed options."""
        return NOT_CLASSIFIED

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        return None

    def _parse_end(self, item):
        """Parse end datetime as a naive datetime object. Added by pipeline if None"""
        return None

    def _parse_time_notes(self, item):
        """Parse any additional notes on the timing of the meeting"""
        return ""

    def _parse_location(self, item):
        """Parse or generate location."""
        return {
            "address": "",
            "name": "",
        }

    def _parse_links(self, item):
        """Parse or generate links."""
        return [{"href": "", "title": ""}]

    def _parse_source(self, response):
        """Parse or generate source."""
        return response.url
