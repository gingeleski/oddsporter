"""
op.py

OddsPortal scraping utility

"""

from oddsportal import *

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
    crawler = Crawler()
    logger.info('Crawler has been initialized')
    for target_sport_obj in target_sports:
        c_name = target_sport_obj['collection_name']
        logger.info('Starting data collection "' + c_name + '"')
        data.start_new_data_collection(target_sport_obj)
        main_league_results_url = target_sport_obj['root_url']
        working_seasons = crawler.get_seasons_for_league(main_league_results_url)
        for i,_ in enumerate(working_seasons):
            crawler.fill_in_season_pagination_links(working_seasons[i])
        data[c_name].league.seasons = working_seasons
        # TODO request all links in each season with scraped data
    data.set_output_directory(OUTPUT_DIRECTORY_PATH)
    data.save_all_collections_to_json()
    logger.info('Ending scrape of OddsPortal.com')

#######################################################################################################################

if __name__ == '__main__':
    main()
    