"""
Parse excel files with CPI data from Rosstat
"""

import re

import pandas as pd
import requests
from bs4 import BeautifulSoup


class RosstatParser:
    main_url = 'https://rosstat.gov.ru'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/87.0.4280.88 Safari/537.36',
    }

    def __init__(self, _main_page: str = None, _cpi_page: str = None):
        """
        Create requests session
        """
        self.session = requests.Session()
        self.session.headers.update(RosstatParser.headers)
        self.main_page = _main_page
        self.cpi_page = _cpi_page

    def get_main_page(self):
        """
        Get html with all price data
        """
        r = self.session.get(RosstatParser.main_url + '/price')
        r.raise_for_status()
        self.main_page = r.text

    @staticmethod
    def get_tables(page: str) -> list:
        """
        Get links to all .xlsx files on the page
        """
        soup = BeautifulSoup(page, 'html.parser')
        regexp = f'^{RosstatParser.main_url}' + '/storage/mediabank/.{8}/.+.xlsx$'
        tables = [link.get('href') for link in soup.find_all('a', href=re.compile(regexp))]
        return tables

    @staticmethod
    def update_cpi(tables: list):
        """
        Update CPI data in the database
        """
        titles = ['Товары и услуги', 'Продовольственные товары', 'Непродовольственные товары', 'Услуги']
        for title, table in zip(titles, tables):
            cpi_data = RosstatParser.get_cpi_as_series(table)
            print(title)
            print(cpi_data, end='\n\n')  # df to SQL

    """ CPI parsing """

    def get_cpi(self) -> list:
        """
        Return list of links to CPI tables
        """
        try:
            self.get_main_page()
        except requests.exceptions.HTTPError:
            print('http error caused while getting the main page')
            exit()

        try:
            self.get_cpi_page()
        except requests.exceptions.HTTPError:
            print('http error caused while getting the cpi page')
            exit()

        return RosstatParser.get_tables(self.cpi_page)

    def get_cpi_url(self):
        """
        Get url to html with CPI data
        """
        soup = BeautifulSoup(self.main_page, 'html.parser')
        regexp = '^/storage/mediabank/.{8}/Индексы потребительских цен по Российской Федерации.html$'
        cpi_tag = soup.find('a', href=re.compile(regexp),
                            class_='btn btn-icon btn-white btn-br btn-sm', target='_blank')
        return cpi_tag.get('href')

    def get_cpi_page(self):
        """
        Get html with CPI data
        """
        r = self.session.get(RosstatParser.main_url + self.get_cpi_url())
        r.raise_for_status()
        self.cpi_page = r.text

    """ CPI data processing """

    @staticmethod
    def process_cpi(df: pd.DataFrame) -> pd.Series:
        """
        Clean and reformat dataframe with CPI data
        """
        months = [
            'January', 'February',
            'March', 'April', 'May',
            'June', 'July', 'August',
            'September', 'October', 'November',
            'December', 'lastDecember'
        ]

        df.dropna(how='all', inplace=True)
        df.columns = df.columns.astype('str')
        df = df.apply(lambda vals: vals.astype('str').str.strip('()').str.replace(',', '.').astype('float'))
        df.index = months

        df.drop('lastDecember', inplace=True)  # temporarily

        unstacked_df = df.unstack()
        dates = [f'{ind[0]} {ind[1]}' for ind in unstacked_df.index]
        return pd.Series(unstacked_df.values, index=pd.to_datetime(dates))

    @staticmethod
    def get_cpi_as_series(link: str) -> pd.Series:
        """
        Return series [date -> CPI value (in relation to the previous month)]
        """
        df = pd.read_excel(link, index_col=0, header=3, skipfooter=1)
        return RosstatParser.process_cpi(df)


if __name__ == '__main__':
    parser = RosstatParser()
    links = parser.get_cpi()
    parser.update_cpi(links)
