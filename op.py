"""
op.py

OddsPortal scraping utility

"""

from models import DataRepository
#from oddsportal import crawler
#from oddsportal import scraper

import json
import logging
import time

#######################################################################################################################

TARGET_SPORTS_FILE = 'config/sports.json'
OUTPUT_DIRECTORY_PATH = 'output'

#######################################################################################################################

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', \
                    handlers=[ logging.FileHandler('logs/oddsportal_' + str(int(time.time())) + '.log'),\
                               logging.StreamHandler() ])
logger = logging.getLogger('oddsportal')

data = DataRepository()

#######################################################################################################################

def get_target_sports_from_file():
    with open(TARGET_SPORTS_FILE) as json_file:
        data = json.load(json_file)
        return data

def main():
    global logger, data
    logger.info('Starting scrape of OddsPortal.com')
    target_sports = get_target_sports_from_file()
    logger.info('Loaded configuration for ' + str(len(target_sports)) + ' sports\' results to scrape')
    for target_sport_obj in target_sports:
        data.start_new_data_collection(target_sport_obj)
    #c = crawler.Crawler(headless=False)
    #d = c.leagues('handball')
    #print(d)
    #l = c.league_links(d)
    #print(l)
    #s = scraper.Scraper(headless=False)
    #for k,links in d.items():
    #    s.get_data(l, args.scrape[1], args.scrape[2])
    logger.info('Ending scrape of OddsPortal.com')

#######################################################################################################################

if __name__ == '__main__':
    main()
    