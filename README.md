# Stock Scrapper

## Problem Statement

The scraper will take an input of 10 twitter accounts, it will scrape them every X minutes looking for mentions of stock symbols.

- This is what a stock symbol looks like on Twitter: \$TSLA – there will always be a Cashtag "\$" before it
- Your script inputs should be
    - List of Twitter Accounts 
    - Ticker (the $ with a 4 or 3 letter word) to look for
    - The time interval for another scraping session
- The output displayed should be:
    - The number of times the stock symbol was mentioned
    - Stock Symbol (e.g. $TSLA, $SOFI, $APPL, etc.)
    - The time interval used

Output example: "\$TSLA was mentioned ten times in the last 15 minutes."

Use these 10 Twitter accounts:

- https://twitter.com/Mr_Derivatives 
- https://twitter.com/warrior_0719
- https://twitter.com/ChartingProdigy
- https://twitter.com/allstarcharts
- https://twitter.com/yuriymatso
- https://twitter.com/TriggerTrades
- https://twitter.com/AdamMancini4 
- https://twitter.com/CordovaTrades 
- https://twitter.com/Barchart
- https://twitter.com/RoyLMattox

Your tool and code should be clear, well-commented, and well-structured. You’re free to use packages and libraries, but don’t use APIs.

## Example Use

```sh
python -m pip install -r requirements.txt
python run.py
curl -X POST -H "Content-Type: application/json" -d @sample_input.json http://127.0.0.1:5000/count-patterns-interval
```