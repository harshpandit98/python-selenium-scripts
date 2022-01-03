# scrapy-spiders
Repository containing web scrapers.

# setup guide

clone with ssh repo url to a directory
- `git clone --single-branch --branch add/haryanareragovin git@github.com:harshpandit98/python-selenium-scripts.git`

create virtualenv (python 3.8 or higher prefered)
- `virtualenv venv`

activate virtualenv
- `source ./venv/bin/active`

install requirements
- `pip install -r requirements.txt`

run example
- `python haryanareragovin.py --district_name=GURUGRAM --headless=0`

parameters:
- --district_name: district name

- --headless: wether to run in headless mode or headful.
    0: run in headful mode
    1: run in headless mode