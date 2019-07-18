"""
crawler.py

Logic for the overall OddsPortal scraping utility focused on crawling

"""


from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

import logging


logger = logging.getLogger(__name__)


class Crawler(object):
    """
    A class to crawl links from oddsportal.com website.
    Makes use of Selenium and BeautifulSoup modules.
    """
    WAIT_TIME = 3  # max waiting time for a page to load
    
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
        
    def get_html_source(self):
        return self.driver.page_source
    
    def close_browser(self):
        self.driver.quit()
        logger.info('browser closed')
    
    def get_league_seasons(self, league_link):
        '''
        league_link: eg.: http://www.oddsportal.com/handball/austria/hla/results/
        
        Returns a list of links.
        '''
        p_links = []
        
        if not self.go_to_link(league_link):
            return []
        
        html_source = self.get_html_source()
        soup = BeautifulSoup(html_source, "html.parser")
        
        seasons = soup.find("div", class_="main-menu2 main-menu-gray").find_all("span")
        
        season_links = [season.find("a")['href'] for season in seasons]
        
        logger.info('season links in league: %s', season_links)
        
        for link in season_links:
            self.go_to_link(self.base_url + link)
            p_links.append(self.pagination(link))
        
        # flatten the results
        return [item for sublist in p_links for item in sublist]
    
    def get_season_pagination_links(self, season_link):
        '''
        Returns the page's pagination of a single season on the Odds Portal website.
        
        eg.: season_link = '/handball/austria/hla-2017-2018/results/' 
        
        Returns a list of links.
        '''
        pagination_links = []
        
        self.go_to_link(self.base_url + season_link)
        html_source = self.get_html_source()
        soup = BeautifulSoup(html_source, "html.parser")
        pagination_tags = soup.find("div", id="pagination")
        
        # no pagination for this link
        if pagination_tags is None:
            pagination_links.append(self.base_url + season_link)
        else:
            pagination_links.append(self.base_url + season_link)
            paginations = [page['href'] for page in pagination_tags.find_all("a")]
            
            for page in paginations:
                if page.find('page') != -1:
                    if (self.base_url + season_link + page) not in pagination_links:
                        pagination_links.append(self.base_url + season_link + page)
                    
        logger.info('pagination links: %s', pagination_links)
        
        return pagination_links


if __name__ == '__main__':
    c = Crawler()
    c.go_to_link('https://www.oddsportal.com')
    print(c.get_html_source())
    c.close_browser()
