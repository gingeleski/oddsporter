#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 18 19:25:00 2018

@author:
"""

import argparse
import json
import os
import logging.config
import sys

from oddsportal import crawler
from oddsportal import scraper

def main():
    logging.basicConfig(filename=os.path.join(os.getcwd(),'log/ops.log'),
                        level=logging.WARNING, 
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
                        datefmt="%Y-%m-%d %H:%M:%S")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--tz",
                        help = "set the Time Zone",
                        action="store_true")
    parser.add_argument("--sport",
                        nargs = '+',
                        help = "returns all leagues in a given sport.\n \
                                additional argument save the file to json, if omitted prints to console\n \
                                e.g.: --sport handball output.json")
    parser.add_argument("--sport-links",
                        nargs = 2,
                        help = "returns all the links in a given sport.\n \
                                additional argument save the file to json\n \
                                e.g.: --sport-links handball output.json")
    parser.add_argument("--links-from-file", # ez tuti nem a legjobb elnezvezés
                        nargs = 2,
                        help = "returns all the links for specified leagues\n \
                                e.g.: --links-from-file input.json output.json")
    parser.add_argument("--scrape",
                        nargs = 3,
                        type = str,
                        help = "get all the results and export it into a sql3 db\n \
                                args: input.json database table_name\n \
                                e.g.: --scrape input.json bets.db3 soccer")
    args = parser.parse_args()
    
    # ap = vars(args) # convert arguments into dict and then use ap['test']
    
    # crawler
    if args.sport or args.sport_links or args.links_from_file:
        c = crawler.Crawler(headless=False)
    
        if args.sport:
            d = c.leagues(args.sport[0])
            if len(args.sport)>1:
                with open(args.sport[1], 'w') as fp:
                    json.dump(d, fp, indent=4)
            else:
                print(d)
                
        if args.sport_links:
            d = c.leagues(args.sport_links[0])
            l = c.league_links(d)
            with open(args.sport_links[1],'w') as fp:
                json.dump(l, fp, indent=4)
                
        if args.links_from_file:
            f = open(args.links_from_file[0])
            leagues_dict = json.load(f)
            f.close()
            d = c.league_links(leagues_dict)
            
            with open(args.links_from_file[1], 'w') as fp:
                json.dump(d, fp, indent=4)
        
        c.close_browser()
    
    # scraper
    if args.tz or args.scrape:
        s = scraper.Scraper(headless=False)
        
        if args.tz:
            s.set_time_zone()
            
        if args.scrape:
            f = open(args.scrape[0])
            d = json.load(f)
            f.close()
            
            for k,links in d.items():
                s.get_data(links, args.scrape[1], args.scrape[2])
            
        s.close_browser()

            
if __name__ == '__main__':
    # python 3 required
    if sys.version_info < (3,6):
        raise Exception("must use python 3.6 or higher")
    
    main()
    
