# CPI parser

> Project work on the academic practice of the 2nd year of the HSE university

## Description

[Rosstat](https://rosstat.gov.ru/) web-scrapper 
for obtaining official published inflation values.
As a final product, monthly **cron-job** 
for collecting and updating data has been implemented.

## Technology stack

- python3
- requests
- BeautifulSoup
- pandas, numpy

## Launch instruction

1. Install [python3](https://www.python.org/) 

2. Clone the repository and change the directory
   ```bash
   $ git clone https://github.com/sd-denisoff/cpi-parser.git && cd cpi-parser
   ```
   
3. Create a virtual environment and activate it
   ```bash
   $ virtualenv --python=python3 venv
   $ source venv/bin/activate
   ```

4. Install dependencies
   ```bash
   $ pip3 install -r requirements.txt
   ```

5. Run the script
   ```bash
   $ python3 rosstat_parser.py
   ```
  
Developed by [Stepan Denisov](https://t.me/sd_denisoff 'telegram')