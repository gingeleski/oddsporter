"""
op.py

OddsPortal scraping utility

"""

from joblib import delayed
from joblib import Parallel
from oddsportal import Crawler
from oddsportal import DataRepository
from oddsportal import Scraper

import argparse
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

wait_on_page_load = 3 # seconds - default wait time for each page to load completely

#######################################################################################################################

def get_target_sports_from_file():
    with open(TARGET_SPORTS_FILE) as json_file:
        data = json.load(json_file)
        return data

def scrape_games_for_season(this_season):
    global wait_on_page_load
    logger.info('Season "%s" - getting all pagination links', this_season.name)
    crawler = Crawler(wait_on_page_load=wait_on_page_load)
    logger.info('Season "%s" - started this crawler', this_season.name)
    crawler.fill_in_season_pagination_links(this_season)
    crawler.close_browser()
    logger.info('Season "%s" - closed this crawler', this_season.name)
    logger.info('Season "%s" - populating all game data via pagination links', this_season.name)
    scraper = Scraper(wait_on_page_load=wait_on_page_load)
    logger.info('Season "%s" - started this scraper', this_season.name)
    scraper.populate_games_into_season(this_season)
    scraper.close_browser()
    logger.info('Season "%s" - closed this scraper', this_season.name)
    return this_season

def main():
    global logger, data, wait_on_page_load
    # Instantiate the argument parser
    parser = argparse.ArgumentParser(description='oddsporter v1.0')
    # Declaring all our acceptable arguments below...
    parallel_cpus_desc = 'Number parallel CPUs for processing (default -1 for max available)'
    parser.add_argument('--number-of-cpus', type=int, nargs='?', help=parallel_cpus_desc)
    parser.add_argument('--wait-time-on-page-load', type=int, nargs='?', help='How many seconds to wait on page load (default 3)')
    # Then grab them from the command line input
    # START parsing command line arguments and logging what's happening
    args = parser.parse_args()
    max_parallel_cpus = args.number_of_cpus
    if max_parallel_cpus == None:
        logger.info('Did not receive argument --number-of-cpus so will use maximum available to crawl and scrape')
        max_parallel_cpus = -1
    else:
        logger.info('Received argument --number-of-cpus so will use %s', str(max_parallel_cpus))
    if args.wait_time_on_page_load != None:
        wait_on_page_load = args.wait_time_on_page_load
        logger.info('Received argument --wait-time-on-page-load so will wait %s seconds', str(wait_on_page_load))
    else:
        logger.info('Did not receive argument --wait-time-on-page-load so will use default 3 seconds')
    # END parsing command line arguments and logging what's happening
    logger.info('Starting scrape of OddsPortal.com')
    target_sports = get_target_sports_from_file()
    logger.info('Loaded configuration for ' + str(len(target_sports)) + ' sports\' results to scrape')
    crawler = Crawler(wait_on_page_load=wait_on_page_load)
    logger.info('Crawler for season links has been initialized')
    for target_sport_obj in target_sports:
        c_name = target_sport_obj['collection_name']
        logger.info('Starting data collection "%s"', c_name)
        data.start_new_data_collection(target_sport_obj)
        main_league_results_url = target_sport_obj['root_url']
        working_seasons = crawler.get_seasons_for_league(main_league_results_url)
        crawler.close_browser()
        logger.info('Crawler for season links has been shut down')
        # Make sure possible outcomes field is set, because the parallel processor needs to know
        for i,_ in enumerate(working_seasons):
            working_seasons[i].possible_outcomes = target_sport_obj['outcomes']
        # Use parallel processing to scrape games for each season of this league's history
        working_seasons_w_games = Parallel(n_jobs=max_parallel_cpus)(delayed(scrape_games_for_season)(this_season) for this_season in working_seasons)
        data[c_name].league.seasons = working_seasons_w_games
    data.set_output_directory(OUTPUT_DIRECTORY_PATH)
    data.save_all_collections_to_json()
    logger.info('Ending scrape of OddsPortal.com')

#######################################################################################################################

if __name__ == '__main__':
    main()
    