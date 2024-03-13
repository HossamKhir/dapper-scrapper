import re
import threading
import time
from collections import Counter
from functools import partial
from multiprocessing import Pool, cpu_count

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
    """_summary_

    :param urls: _description_
    :type urls: list[str]
    :param patterns: _description_
    :type patterns: list[str]
    :return: _description_
    :rtype: tuple[dict[str, int], list[str]]
    """
    result_dict = {pattern: 0 for pattern in patterns}
    result_list = []
    errors = []
    for url in urls:
        result, error = collect_patterns_from_url(url, patterns)
        if result:
            result_list.extend(result)
        if error:
            errors.append(error)

    result_dict.update(Counter(result_list))
    return result_dict, errors


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
    result_dict = {pattern: 0 for pattern in patterns}
    result_list = []
    errors = []
    for result, error in results:
        if result:
            result_list.extend(result)
        if error:
            errors.append(error)

    result_dict.update(Counter(result_list))
    return result_dict, errors


def log_pattern_mentions(
    urls: list[str], patterns: list[str], interval: int, stop_event: threading.Event
):
    """_summary_

    :param urls: _description_
    :type urls: list[str]
    :param patterns: _description_
    :type patterns: list[str]
    :param interval: _description_
    :type interval: int
    :param stop_event: _description_
    :type stop_event: threading.Event
    """
    previous_count = Counter(dict.fromkeys(patterns, 0))

    while not stop_event.is_set():
        current_count, _ = count_patterns_in_urls(urls, patterns)
        for pattern in patterns:
            last_t_count = current_count[pattern] - previous_count[pattern]
            print(f"{pattern} mentioned {last_t_count} times last {interval} minutes")

        previous_count = current_count
        time.sleep(interval * 60)
