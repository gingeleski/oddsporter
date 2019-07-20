"""
scraper.py

Logic for the overall Odds Portal scraping utility focused on scraping

"""


from pyquery import PyQuery as pyquery
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import datetime
import logging
import os
import re
import time


logger = logging.getLogger(__name__)


# https://code.activestate.com/recipes/52308/
class CellData(object):
    """
    strucutre for cell data
    """
    def __init__(self, **kwds):
        #dict.__init__(self,kwds)
        self.__dict__.update(kwds)


class Game(object):
    def __init__(self):
        self.retrieval_url = str()
        self.retrieval_datetime = str()
        self.game_datetime = str()
        self.info_string = str()
        self.num_possible_outcomes = str()
        self.team_home = str()
        self.team_away = str()
        self.odds_home = str()
        self.odds_away = str()
        self.odds_draw = str()
        self.outcome = str()


class Scraper(object):
    """
    A class to scrape/parse match results from oddsportal.com website.
    Makes use of Selenium and BeautifulSoup modules.
    """
    
    def __init__(self):
        """
        Constructor
        """
        self.base_url = 'https://www.oddsportal.com'
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('headless')
        self.driver = webdriver.Chrome('./chromedriver/chromedriver',chrome_options=self.options)
        logger.info('Chrome browser opened in headless mode')
        
        # exception when no driver created
        
    def go_to_link(self,link):
        """
        returns True if no error
        False whe page not found
        """
        # load the page fully
        self.driver.get(link)
        try:
            # if no Login button -> page not found
            self.driver.find_element_by_css_selector('.button-dark')
        except NoSuchElementException:
            logger.warning('problem with link: %s', link)
            return False
        
        return True
        
    def get_html_source(self):
        return self.driver.page_source
    
    def close_browser(self):
        self.driver.quit()
        logger.info('browser closed')

    def populate_games_into_season(self, season):
        """
        Params:
            season (Season) with urls but not games populated, to modify
        """
        for url in season.urls:
            self.go_to_link(url)
            html_source = self.get_html_source()
            html_querying = pyquery(html_source)
            tournament_table = html_querying.find('div#tournamentTable > table#tournamentTable')
            table_rows = tournament_table.find('tbody > tr')
            for table_row in table_rows:
                time_cell = table_row.find('td.table-time')
                if time_cell == None or len(time_cell) < 1:
                    # This row of the table does not contain game/match data
                    continue
                # TODO
    
    def convert_date(self, date):
        """        
        input:
            Today, 26 Sep
            Yesterday, 25 Sep
            19 Sep 2018
            
        return: None if the dat like Today otherwise the date in a from yyyy-mm-dd
        """
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
    
    def cells_data_3way(self, table):
        """
        returns the match's details in a list of struct [CellData1, CellData2, ...]
        for 3 way sports like soccer, handball ...
        """
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

    def get_data(self, links):
        """
        get_data
        """
        total_rows = len(links)
        k = 0
        # get all the data
        for link in links:
            self.go_to_link(link)
            html_source = self.get_html_source()
            soup = BeautifulSoup(html_source, 'html.parser')
            # get the table which contains the results 
            table = soup.find('table', id='tournamentTable')
            data = self.cells_data_3way(table)
            if data:
                for d in data:
                    # save to database
                    teams = d.teams.split(" - ")
                    print([d.url, d.date, d.hour, teams[0], teams[1], d.score, d.odds_home, d.odds_draw, d.odds_away, d.result])


if __name__ == '__main__':
    with open('nba_1.html', 'r') as afile:
        html_source = afile.read()
    # From here, start actionable code for the real Scraper class...
    number_of_outcomes = 2
    html_querying = pyquery(html_source)
    retrieval_time_for_reference = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    tournament_table = html_querying.find('div#tournamentTable > table#tournamentTable')
    table_rows = tournament_table.find('tbody > tr')
    num_table_rows = len(table_rows)
    for i in range(0,num_table_rows):
        # Finding the table cell with game time and assessing if its blank tells us if this is a game data row
        time_cell = tournament_table.find('tbody > tr').eq(i).find('td.table-time')
        if 0 == len(str(time_cell).strip()):
            # This row of the table does not contain game/match data
            continue
        game = Game()
        # Need to get the actual HtmlElement out of the PyQuery object that time_cell currently is
        time_cell = time_cell[0]
        for key, value in time_cell.attrib.items():
            if key == 'class':
                time_cell_classes = value.split(' ')
                for time_cell_class in time_cell_classes:
                    if 0 == len(time_cell_class) or time_cell_class[0] != 't':
                        continue
                    if time_cell_class[1] == '0' or time_cell_class[1] == '1' or time_cell_class[2] == '2':
                        unix_time = int(time_cell_class.split('-')[0].replace('t',''))
                        game.game_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(unix_time))
                        break
                break
        # If time still isn't set at this point, then assume corrupt data and skip the row
        if 0 == len(game.game_datetime):
            continue
        # Set some of the other Game fields that are easy to fill in
        game.retrieval_datetime = retrieval_time_for_reference
        game.retrieval_url = 'https://www.oddsportal.com' # TODO FIXME put the real URL here
        game.num_possible_outcomes = number_of_outcomes
        # Now get the table cell with participants
        participants_cell = tournament_table.find('tbody > tr').eq(i).find('td.table-participant')
        # TODO
        # Now get the table cell with overall odds
        overall_odds_cell = tournament_table.find('tbody > tr').eq(i).find('td.table-odds')
        # TODO
        # Finally, get the cells with odds - either 2 or 3 depending on number of possible outcomes
        individual_odds_cells = tournament_table.find('tbody > tr').eq(i).find('td.odds-nowrp')
        if 2 == number_of_outcomes:
            # TODO
            pass
        elif 3 == number_of_outcomes:
            # TODO
            pass
        else:
            raise RuntimeError('Unsupported number of outcomes specified - ' + str(number_of_outcomes))
        exit()
        