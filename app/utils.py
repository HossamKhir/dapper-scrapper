import re
import threading
import time
from collections import Counter
from functools import partial
from multiprocessing import Pool, cpu_count

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from config import logger

CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument("--headless")


def initialize_webdriver():
    """
    Initialize a new instance of the Chrome WebDriver.

    This function creates and returns a new instance of the Chrome WebDriver using predefined Chrome options.
    It requires the `selenium` WebDriver package and assumes that `CHROME_OPTIONS` are already set up
    with the desired settings.

    :return: An instance of Chrome WebDriver with the specified options.
    :rtype: selenium.webdriver.Chrome
    """
    return webdriver.Chrome(options=CHROME_OPTIONS)


def collect_patterns_from_url(
    url: str,
    patterns: list[str],
    tag="a",
    class_name="css-1qaijid r-bcqeeo r-qvutc0 r-poiln3 r-1loqt21",
) -> tuple[list[str], str]:
    """
    Scans the HTML of a given URL for elements with specified tag and class name to
    extract and return all occurrences of given patterns.

    This function initializes a WebDriver instance to load the webpage and then utilizes
    BeautifulSoup for parsing the HTML content. The search is case-insensitive.

    :param url: The web address to scan for patterns.
    :type url: str
    :param patterns: A list of string patterns to search for within the webpage's text.
    :type patterns: list[str]
    :param tag: The type of HTML tag to look within for the patterns, defaults to "a".
    :type tag: str, optional
    :param class_name: The class attribute of the HTML tag to narrow the search, defaults to
                       "css-1qaijid r-bcqeeo r-qvutc0 r-poiln3 r-1loqt21".
    :type class_name: str, optional
    :return: A tuple containing a list of matched patterns found and an error message
             (empty if no error occurs).
    :rtype: tuple[list[str], str]

    The function returns an empty list and an error message if an exception occurs.
    Otherwise, it will return a list of found patterns (case converted to upper)
    and an empty string for the error message.
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
    """
    Counts the occurrences of each pattern within a list of URLs,
    and also records any errors encountered during the process.

    :param urls: A list of URLs to search for the patterns.
    :type urls: list[str]
    :param patterns: A list of string patterns to count in the URLs.
    :type patterns: list[str]
    :return: A tuple containing a dictionary of pattern counts
             and a list of errors. Each key in the dictionary is a
             pattern from the input list, and the associated value is
             the count of occurrences of that pattern across all provided URLs.
             The errors list contains any issues encountered,
             as strings describing the error.
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
    """
    Periodically logs the number of times each pattern is mentioned on the web pages at the given URLs.

    This function runs a loop that, at each `interval` of minutes, checks the frequency of each
    pattern in the `patterns` list within the content found at each URL in the `urls` list.
    The loop continues until the `stop_event` is set. In each iteration, the function logs the increase
    in the count of pattern mentions compared to the previous check.

    :param urls: A list of URLs as strings to search for pattern occurrences.
    :type urls: list[str]
    :param patterns: A list of string patterns to search for within the content of the URLs.
    :type patterns: list[str]
    :param interval: Time interval in minutes between each log output.
    :type interval: int
    :param stop_event: A threading.Event that, when set, will break the loop and stop the function.
    :type stop_event: threading.Event
    """
    previous_count = Counter(dict.fromkeys(patterns, 0))

    while not stop_event.is_set():
        current_count, _ = count_patterns_in_urls(urls, patterns)
        for pattern in patterns:
            last_t_count = current_count[pattern] - previous_count[pattern]
            print(f"{pattern} mentioned {last_t_count} times last {interval} minutes")
            logger.info(
                f"{pattern} mentioned {last_t_count} times last {interval} minutes"
            )

        previous_count = current_count
        time.sleep(interval * 60)
