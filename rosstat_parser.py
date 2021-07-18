"""
Parse CPI data from Rosstat excel files
"""

import logging
import re
from typing import List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)


class RosstatParser:
    MAIN_URL = 'https://rosstat.gov.ru'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    }

    def __init__(self):
        """
        Create requests session
        """
        self.session = requests.Session()
        self.session.headers.update(RosstatParser.HEADERS)

    def __call__(self, *args, **kwargs) -> Optional[List[str]]:
        """
        Get list of links to tables with CPI data
        """
        try:
            self.get_main_page()
        except requests.exceptions.HTTPError as e:
            logging.error(f'HTTP error caused while getting the MAIN page: {e}')
            return
        try:
            self.get_cpi_page()
        except requests.exceptions.HTTPError as e:
            logging.error(f'HTTP error caused while getting the CPI page: {e}')
            return
        return RosstatParser.get_excel_tables(self.cpi_page)

    def get_main_page(self):
        """
        Get html with all rosstat price data
        """
        r = self.session.get(f'{RosstatParser.MAIN_URL}/price')
        r.raise_for_status()
        self.main_page = r.text

    def get_cpi_page(self):
        """
        Get html with CPI data
        """
        r = self.session.get(f'{RosstatParser.MAIN_URL}{self.get_cpi_url()}')
        r.raise_for_status()
        self.cpi_page = r.text

    def get_cpi_url(self) -> str:
        """
        Get url to html with CPI data
        """
        soup = BeautifulSoup(self.main_page, 'html.parser')
        regexp = '^/storage/mediabank/.{8}/Индексы потребительских цен.html$'
        link_tag = soup.find('a', href=re.compile(regexp))
        return link_tag.get('href')

    @staticmethod
    def get_excel_tables(html_page: str) -> List[str]:
        """
        Get links to all .xlsx files on the html page
        """
        soup = BeautifulSoup(html_page, 'html.parser')
        regexp = '^' + RosstatParser.MAIN_URL + '/storage/mediabank/.{8}/.+.xlsx$'
        tables = [link.get('href') for link in soup.find_all('a', href=re.compile(regexp))]
        return tables

    """ CPI data processing """

    @staticmethod
    def get_cpi_data(link: str) -> pd.Series:
        """
        Return series [date -> CPI value] (in relation to the previous month)
        """
        df = pd.read_excel(link, engine='openpyxl', index_col=0, header=3, skipfooter=1)
        return RosstatParser.data_processing(df)

    @staticmethod
    def data_processing(df: pd.DataFrame) -> pd.Series:
        """
        Clean and reformat dataframe with CPI data
        """
        months = [
            'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
            'September', 'October', 'November', 'December', 'lastDecember'
        ]

        df.dropna(how='all', inplace=True)
        df.columns = df.columns.astype('str')
        df = df.apply(lambda vals: vals.astype('str').str.strip('()').str.replace(',', '.').astype('float'))
        df.index = months

        df.drop('lastDecember', inplace=True)  # temporary drop, requires special handling

        unstacked_df = df.unstack()
        dates = [f'{timestamp[0]} {timestamp[1]}' for timestamp in unstacked_df.index]
        return pd.Series(unstacked_df.values, index=pd.to_datetime(dates))

    """ Updater """

    @staticmethod
    def update_cpi(tables: List[str]):
        """
        Update CPI data in the database
        """
        titles = ['goods_and_services', 'food_products', 'non_food_products', 'services']
        for title, table in zip(titles, tables):
            cpi_data = RosstatParser.get_cpi_data(table)
            # SQL


if __name__ == '__main__':
    parser = RosstatParser()
    cpi_tables_links = parser()
    logging.info(f'Web-scrapping result: {cpi_tables_links}')
    RosstatParser.update_cpi(cpi_tables_links)
    logging.info(f'CPI data has been updated in DB!')
