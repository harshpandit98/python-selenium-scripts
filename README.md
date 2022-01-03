# Setup guide

Clone with ssh repo url to a directory
- `git clone --single-branch --branch add/haryanareragovin git@github.com:harshpandit98/python-selenium-scripts.git`

Create virtualenv (python 3.8 or higher prefered)
- `virtualenv venv`

Activate virtualenv
- `source ./venv/bin/active`

Install requirements
- `pip install -r requirements.txt`

Run example
- `python haryanareragovin.py --district_name=GURUGRAM --headless=0`

Parameters:
- --district_name: district name

- --headless: 0 - run in headful mode, 1 - run in headless mode
