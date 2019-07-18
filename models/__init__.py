"""
models/__init__.py

OddsPortal crawling/scraping data models

"""


class Game(object):
    def __init__(self):
        self.retrieval_url = str()
        self.retrieval_date = str()
        self.retrieval_time = str()
        self.game_date = str()
        self.game_time = str()
        self.game_note = str()
        self.info_string = str()
        self.num_possible_outcomes = str()
        self.team_home = str()
        self.team_away = str()
        self.odds_home = str()
        self.odds_away = str()
        self.odds_draw = str()
        self.outcome = str()


class Season(object):
    def __init__(self,name):
        self.name = name
        self.games = list()

    def add_game(self,game):
        self.games.append(game)


class League(object):
    def __init__(self,name):
        self.name = name
        self.seasons = dict()
        self.root_url = str()
        self.links = list()

    def __getitem__(self,key):
        return self.seasons[key]

    def __setitem__(self,key,value):
        self.seasons[key] = value

class Collection(object):
    def __init__(self,name):
        self.name = name
        self.sport = str()
        self.region = str()
        self.output_dir = str()
        self.parse_type = str()
        self.league = None

    def __getitem__(self,key):
        return self.league[key]

    def __setitem__(self,key,value):
        self.league[key] = value


class DataRepository(object):
    def __init__(self):
        self.collections = dict()

    def start_new_data_collection(self,target_sport_obj):
        if target_sport_obj['collection_name'] not in self.collections:
            # Most fields from "target sport objects" map to Collection fields
            new_collection = Collection(target_sport_obj['collection_name'])
            new_collection.sport = target_sport_obj['sport']
            new_collection.region = target_sport_obj['region']
            new_collection.output_dir = os.path.normpath('output' + os.sep + target_sport_obj['output_dir'])
            new_collection.parse_type = target_sport_obj['parse_type']
            # *Some* fields from "target sport objects" map to League fields
            new_league = League(target_sport_obj['league'])
            new_league.root_url = target_sport_obj['root_url']
            new_collection.league = new_league
            # Store this new Collection in this repository, by name
            self.collections[target_sport_obj['collection_name']] = new_collection
        else:
            raise RuntimeError('Target sports JSON file must have unique collection names.')

    def save_all_collections_to_json(self):
        for _, collection in self.collections.items():
            if os.path.isdir(collection.output_dir):
                filelist = [ f for f in os.listdir(collection.output_dir) ]
                for f in filelist:
                    os.remove(os.path.join(collection.output_dir, f))
            else:
                os.makedirs(collection.output_dir)
            with open(os.path.join(collection.output_dir, collection.name + '.json')) as outfile:
                json.dump(collection, outfile)

    def __getitem__(self,key):
        return self.collections[key]

    def __setitem__(self,key,value):
        self.collections[key] = value
