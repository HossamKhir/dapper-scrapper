#! /usr/bin/env python3
"""
"""
import re
import time
from collections import Counter
from functools import partial
from multiprocessing import Pool
from os import cpu_count

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument("--headless")


def initialize_webdriver():
    """_summary_

    :return: _description_
    :rtype: _type_
    """
    return webdriver.Chrome(options=CHROME_OPTIONS)


def collect_patterns_from_url(
    url: str,
    patterns: list[str],
    tag="a",
    class_name="css-1qaijid r-bcqeeo r-qvutc0 r-poiln3 r-1loqt21",
) -> tuple[list[str], str]:
    """_summary_

    :param url: _description_
    :type url: str
    :param patterns: _description_
    :type patterns: list[str]
    :param tag: _description_, defaults to "a"
    :type tag: str, optional
    :param class_name: _description_, defaults to "css-1qaijid r-bcqeeo r-qvutc0 r-poiln3 r-1loqt21"
    :type class_name: str, optional
    :return: _description_
    :rtype: tuple[list[str], str]
    """
    driver = initialize_webdriver()
    try:
        # use selenium to get page source
        driver.get(url)
        # allow the page to fully load
        time.sleep(5)
        html = driver.page_source
    except Exception as e:
        return [], str(e)
    finally:
        # always close the browser
        driver.quit()

    # parse HTML w/ BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # find all html entities w/ the class name
    elements = soup.find_all(tag, class_=class_name)

    # concatenate their strings and search for the pattern
    concatenated = " ".join([element.get_text() for element in elements])
    pattern = "|".join([f"(?:{re.escape(pattern.upper())})" for pattern in patterns])
    result = re.findall(pattern, concatenated, flags=re.IGNORECASE)
    result = list(map(str.upper, result))

    return result, ""


def count_patterns_in_urls(
    urls: list[str], patterns: list[str]
) -> tuple[dict[str, int], list[str]]:
    result_list = []
    errors = []
    for url in urls:
        result, error = collect_patterns_from_url(url, patterns)
        if result:
            result_list.extend(result)
        if error:
            errors.append(error)
    return dict(Counter(result_list)), errors


# FIXME: doesn't always work
def count_patterns_in_urls_concurrently(
    urls: list[str], patterns: list[str]
) -> tuple[dict[str, int], list[str]]:
    """_summary_

    :param urls: _description_
    :type urls: list[str]
    :param patterns: _description_
    :type patterns: list[str]
    :return: _description_
    :rtype: tuple[dict[str, int], list[str]]
    """
    with Pool(processes=cpu_count()) as pool:
        # Create a partial function with the patterns argument filled
        func = partial(collect_patterns_from_url, patterns=patterns)
        # Map the function over the URLs concurrently
        results = pool.map(func, urls)

    # Combine results from all URLs
    result_list = []
    errors = []
    for result, error in results:
        if result:
            result_list.extend(result)
        if error:
            errors.append(error)

    return dict(Counter(result_list)), errors


if __name__ == "__main__":
    urls = [
        "https://twitter.com/Mr_Derivatives",
        "https://twitter.com/warrior_0719",
        "https://twitter.com/CordovaTrades",
        "https://twitter.com/ChartingProdigy",
        "https://twitter.com/allstarcharts",
        "https://twitter.com/yuriymatso",
        "https://twitter.com/TriggerTrades",
        "https://twitter.com/AdamMancini4",
        "https://twitter.com/Barchart",
        "https://twitter.com/RoyLMattox",
    ]
    patterns = ["$TSLA", "$SOFI", "$APPL", "$SPX"]
    begin = time.time()
    res = count_patterns_in_urls_concurrently(urls, patterns)
    end = time.time()
    print(end - begin)
    # res = count_patterns_in_urls(urls, patterns)
    print(res)
