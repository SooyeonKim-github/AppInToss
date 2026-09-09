from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import urlencode
import requests

from ...config import OLIVEYOUNG_CATEGORY_ID, OLIVEYOUNG_REQUEST_INTERVAL_SEC, OLIVEYOUNG_ROWS_PER_PAGE, OLIVEYOUNG_SORT, OLIVEYOUNG_TIMEOUT_SEC, OLIVEYOUNG_USE_SELENIUM, USER_AGENT
from .models import CollectedProduct
from .parser import parse_category_html

CATEGORY_URL = "https://www.oliveyoung.co.kr/store/display/getMCategoryList.do"


@dataclass(slots=True)
class OliveYoungPage:
    page: int
    url: str
    html: str


class OliveYoungClient:
    def __init__(self, *, use_selenium: bool | None = None) -> None:
        self.use_selenium = OLIVEYOUNG_USE_SELENIUM if use_selenium is None else use_selenium
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8", "Referer": "https://www.oliveyoung.co.kr/"})

    @staticmethod
    def build_category_url(page: int, *, sort: str = OLIVEYOUNG_SORT) -> str:
        params = {"dispCatNo": OLIVEYOUNG_CATEGORY_ID, "fltDispCatNo": "", "prdSort": sort, "pageIdx": page, "rowsPerPage": OLIVEYOUNG_ROWS_PER_PAGE, "searchTypeSort": "btn_thumb", "plusButtonFlag": "N", "isLoginCnt": "0", "aShowCnt": "0", "bShowCnt": "0", "cShowCnt": "0", "trackingCd": f"Cat{OLIVEYOUNG_CATEGORY_ID}_Small"}
        return f"{CATEGORY_URL}?{urlencode(params)}"

    def _fetch_requests(self, page: int) -> OliveYoungPage:
        url = self.build_category_url(page)
        response = self.session.get(url, timeout=OLIVEYOUNG_TIMEOUT_SEC)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or response.encoding
        return OliveYoungPage(page=page, url=url, html=response.text)

    def _fetch_selenium(self, page: int) -> OliveYoungPage:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.support.ui import WebDriverWait
        except ImportError as exc:
            raise RuntimeError("selenium이 설치되지 않았습니다. requirements.txt를 설치하세요.") from exc
        url = self.build_category_url(page)
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280,2200")
        options.add_argument(f"--user-agent={USER_AGENT}")
        options.add_argument("--lang=ko-KR")
        driver = webdriver.Chrome(options=options)
        try:
            driver.get(url)
            WebDriverWait(driver, 15).until(lambda d: len(d.find_elements("css selector", "div.prd_info")) > 0)
            return OliveYoungPage(page=page, url=url, html=driver.page_source)
        finally:
            driver.quit()

    def fetch_page(self, page: int) -> OliveYoungPage:
        if self.use_selenium:
            return self._fetch_selenium(page)
        page_data = self._fetch_requests(page)
        if "prd_info" not in page_data.html and "goodsNo=" not in page_data.html:
            return self._fetch_selenium(page)
        return page_data

    def collect(self, pages: int) -> list[CollectedProduct]:
        results: list[CollectedProduct] = []
        seen: set[str] = set()
        for page_no in range(1, pages + 1):
            page = self.fetch_page(page_no)
            for product in parse_category_html(page.html, page.url):
                if product.goods_no in seen:
                    continue
                seen.add(product.goods_no)
                product.rank = len(results) + 1
                results.append(product)
            if page_no < pages:
                time.sleep(OLIVEYOUNG_REQUEST_INTERVAL_SEC)
        return results

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "OliveYoungClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
