"""
scraper.py

Logic for the overall OddsPortal scraping utility focused on scraping

"""

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
import datetime
import os

# import from the same dir
###from . import sqlite_db as sq

# in each module
import logging
logger = logging.getLogger(__name__)

# https://code.activestate.com/recipes/52308/
class CellData(object):
    """
    strucutre for cell data
    """
    def __init__(self, **kwds):
        #dict.__init__(self,kwds)
        self.__dict__.update(kwds)


class Scraper(object):
    """
    A class to scrape/parse match results from oddsportal.com
    """
    
    def __init__(self, headless=True, browser='firefox'):
        """
        Constructor providing the executable path value to None
        for now only firefox
        for Firefox headless gecko driver required
        """
        self.base_url = 'http://www.oddsportal.com'
        
        if browser == 'firefox':
            if headless:
                self.option = webdriver.firefox.options.Options()
                self.option.add_argument('-headless')
                self.driver = webdriver.Firefox(firefox_options=self.option)
                logger.info('browser opened in headless mode')
            else:
                self.driver = webdriver.Firefox()
                logger.info('browser opened')
        
        # exception when no driver created
 
    # Print iterations progress
    def _print_progress_bar (self, iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            
        # Sample Usage
        from time import sleep
        # A List of Items
        items = list(range(0, 57))
        l = len(items)
        
        # Initial call to print 0% progress
        printProgressBar(0, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for i, item in enumerate(items):
            # Do stuff...
            sleep(0.1)
            # Update Progress Bar
            printProgressBar(i + 1, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
        # Print New Line on Complete
        if iteration == total: 
            print()
        
    def _go_to_link(self,link):
        '''
        returns True if no error
        False whe page not found
        '''
        # load the page fully
        self.driver.get(link)
        try:
            # if no Login button -> page not found
            self.driver.find_element_by_css_selector('.button-dark')
        except NoSuchElementException:
            logger.warning('problem with link: %s', link)
            return False
        
        return True
        
    def _get_html_source(self):
        return self.driver.page_source
    
    def close_browser(self):
        self.driver.quit()
        logger.info('browser closed')

    def set_time_zone(self, timezone="Budapest"):
        self._go_to_link(self.base_url)
        WebDriverWait(self.driver, self.WAIT_TIME).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#user-header-timezone-expander"))).click()
        WebDriverWait(self.driver, self.WAIT_TIME).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, timezone))).click()
        logger.info('timezone set to: %s', timezone)
    
    def _convert_date(self, date):
        '''        
        input:
            Today, 26 Sep
            Yesterday, 25 Sep
            19 Sep 2018
            
        return: None if the dat like Today otherwise the date in a from yyyy-mm-dd
        '''
        now = datetime.datetime.now()
        m = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        n = ['0'+str(i) if i<10 else str(i) for i in range(1,13)]
        months = dict(zip(m,n))
        l = date.split()
        
        if 'Today,' in l:
            date = None
        elif 'Yesterday,' in l:
            date = '{}-{}-{}'.format(now.year, months[l[-1]], l[1])
        else:
            date = '{}-{}-{}'.format(l[-1], months[l[1]], l[0])
        
        # ?
        #date=datetime.datetime.strptime(current_date_str, "%d %b %Y")
        #return datetime.datetime.strftime(date,"%Y-%m-%d")
        return date
        
    
    def _cells_data_3way(self, table):
        '''
        returns the match's details in a list of struct [CellData1, CellData2, ...]
        for 3 way sports like soccer, handball ...
        '''
        cells = []
        
        isEmpty = table.find("td", id="emptyMsg")
        if not isEmpty:
            for tr in table.find_all("tr"):
                cell = CellData(url=None, date=None, hour=None, teams=None, score=None, 
                                odds_home=None, odds_draw=None, odds_away=None, result=None)
                
                for span in tr.find_all("span",class_=re.compile('datet')):
                    # convert it to yyyy-mm-dd form
                    md = self._convert_date(span.get_text())
                    
                valid_match = False
                for num, td in enumerate(tr.find_all("td")):
                    if num == 0 and td.get_text() != u'':
                        cell.hour = td.get_text()   # Match hours
                        cell.date = md # Match date
                    elif num == 1 and td.get_text() != u'': 
                        cell.teams = td.get_text()  # Teams or Players
                        # TODO maybe split home away here
                        if 'inplay' in td.a['href']:
                            cell.url = None
                        else:
                            cell.url = td.a['href'] # Links to the match details
                    elif num == 2 and td.get_text() != u'':
                        cell.score = td.get_text()  # Score
                    elif num == 3 and td.get_text() != u'':
                        cell.odds_home = td.get_text()  # Average odd for team 1
                        if 'result-ok' in td.get('class') and not valid_match:
                            cell.result = 1 # Team 1 is the winner
                            valid_match = True
                    elif num == 4 and td.get_text() != u'':
                        cell.odds_draw = td.get_text()  # Average odd for draw
                        if 'result-ok' in td.get('class') and not valid_match:
                            cell.result = 0 # Tie
                            valid_match = True
                    elif num == 5 and td.get_text() != u'': 
                        cell.odds_away = td.get_text()  # Average odd for team 2
                        if 'result-ok' in td.get('class') and not valid_match:
                            cell.result = 2
                            valid_match = True
                    elif num == 6 and td.get_text() != u'':
                        #odd_tot.append(td.get_text())  # Number of bookies
                        # if there is no result (match may be cancelled)
                        if not valid_match:
                            cell.result = -1
                
                if cell.hour is not None:
                    logger.info('cell data: %s %s %s %s %s %s', cell.date, cell.hour, cell.url, cell.teams, cell.score, cell.result)
                    cells.append(cell)

            return cells

    def get_data(self, links, db_name, table_name):
        '''
        export the results into sqlite3 db
        
        input: 
            links: a list of links
            db_name: sqlite3 database name. must be in /data
            table_name: if table not exists in d it will be created
        
        e.g.: get_data(['http://www.oddsportal.com/handball/ukraine/superleague/results/'], 'bets.db3', 'handball')
        '''
        
        # connect to db            
        db_file = db_name
        ###con = sq.create_conection(os.path.join(os.getcwd(),'data',db_file))
        logger.info('db version: %s',sq.test_connection(con))
        logger.info('connected to database')
        # check if table exists            
        ###sq.chk_tabe(con, table_name)
        total_rows = len(links)
        k = 0
        # Initial call to print 0% progress
        self._print_progress_bar(k, total_rows, prefix = 'Populate DB:', suffix = 'Complete', length = 50)
        # get all the data
        for link in links:
            self._go_to_link(link)
            html_source = self._get_html_source()
            soup = BeautifulSoup(html_source, "html.parser")
            # get the table which contains the results 
            table = soup.find("table", id="tournamentTable")
            data = self._cells_data_3way(table)
            if data:
                for d in data:
                    # save to database
                    teams = d.teams.split(" - ")
                    ###sq.insert_oddsportal(con, table_name, [d.url, d.date, d.hour, teams[0], teams[1], d.score, d.odds_home, d.odds_draw, d.odds_away, d.result])
                ###con.commit()
            # progress bar
            k += 1
            self._print_progress_bar(k, total_rows, prefix = 'Populate DB:', suffix = 'Complete', length = 50)
        # close db connection
        ###if con:
            ###con.close()
            ###logger.info('database is closed')
        