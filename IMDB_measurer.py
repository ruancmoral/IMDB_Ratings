import requests
from bs4 import BeautifulSoup
import re
import json
from pandas.io.json import json_normalize 

# See : https://www.kaggle.com/jboysen/quick-tutorial-flatten-nested-json-in-pandas/notebook
# 
from datetime import datetime

IMDB_URL = 'https://www.imdb.com'


# Some chars that need to be removed in text (air_date)
REMOVE_CHARS = ['\n','\t',]
rx = '[' + re.escape(''.join(REMOVE_CHARS)) + ']'

class imdb:
    def __init__(self,url):
        self.url = url
        self.soup_show = self.make_request(url)

    def make_request(self,url):
        """ Given a url make a request and return a BeautifulSoup object.
        Parameters: 
            url (str): url target

        Returns:
            BeautifulSoup object if sucessful (200), or None if fail (others)
        """
        response = requests.get(url)
        if response.status_code == 200:
            print('Successful Request at: ', url)
            soup  = BeautifulSoup(response.content,'html.parser')
            return soup
        elif response.status_code == 404:
            print('Not Found.')
        return None

    def scrap_episode(self,epi_tag,season):
        """ Get the div where the episode info is and scrap the usefull content .
        Parameters: 
            epi_tag (BeautifulSoup): object with the content of episode info 
            season  : Season number to insert into the dict
        Returns:
            dict with some info about the episode
            dict_keys = number(episode_number), 
                        info(dict with the info, rating,total_votes,air_date,
                        description,episode_title,season)
        """
        # get the div where the episode info is and scrap the usefull content 
        info = epi_tag.find(attrs={'class':'info'})
        
        # get some info of the episode, can be improved and get more if necessaryY
        air_date = re.sub(rx,' ',info.find(attrs={'class':'airdate'}).get_text()).strip()
        try:
            air_date: datetime.strptime(air_date,'%d %b. %Y')
        except:
            # no specific date to episode, only year
            air_date: datetime.strptime(air_date,'%Y')
        try:
            rating = float(info.find(attrs={'class':'ipl-rating-star__rating'}).get_text())
            total_votes = int(info.find(attrs={'class':'ipl-rating-star__total-votes'}).get_text()[1:-1].replace(',',''))
        except:
            rating = None
            total_votes = None
        episode_number = int(info.find(attrs={'itemprop':'episodeNumber'})['content'])
        episode_description = re.sub(rx,' ',info.find(attrs={'itemprop':'description'}).get_text()).strip()
        episode_title = info.find(attrs={'itemprop':'name'}).get_text()
        episode_info = {
            'episode_number': episode_number,
            'info':{
                'rating': rating,
                'total_votes': total_votes,
                'air_date': air_date,
                'description': episode_description,
                'episode_title': episode_title,
                'season':season,
                'short':season+'.E'+str(episode_number)
                }
            }
        # print(episode_info)
        return episode_info

    def scrap_season_dict(self,season_url):
        """ Given the url of a season of a show, iterate through the episodes and return a dict
        with the info of season and dict of episodes. Episodes are inside of a dict from scrap_episode
        Parameters: 
            season_url (url): Season url (ex: https://www.imdb.com/title/tt1475582/episodes?season=1) 
        Returns:
            dict with some info about the season
            dict_keys = season_txt,total_episodes, Season {number}(dict with episodes) 
        """

        soup_season = self.make_request(season_url)

        # the list of all episodes in imdb page are in a list_item div class
        episodes_html = soup_season.find_all(attrs={'class':'list_item'})

        season_number = soup_season.find(attrs={'id':'episode_top'}).get_text().replace(u'eason\xa0', u'')
        total_episodes = soup_season.find(attrs={'itemprop':'numberofEpisodes'})['content']
        season_info = {
            'season_text':season_number,
            'total_episodes':int(total_episodes),
            }
        for epi in episodes_html:
            episode_info = self.scrap_episode(epi,season_number)
            season_info[episode_info['number']] = episode_info
        # print(season_info)
        return season_info
  
    def scrap_season_array(self,season_url):
        """ Given the url of a season of a show, iterate through the episodes and return a dict 
        with the info of the season, and array of episodes. Episodes are inside of a dict from scrap_episode
        Parameters: 
            season_url (url): Season url (ex: https://www.imdb.com/title/tt1475582/episodes?season=1) 
        Returns:
            dict with some info about the season
            dict_keys = season_txt,total_episodes, Season {number}(array with episodes) 
        """        
        soup_season = self.make_request(season_url)

        # the list of all episodes in imdb page are in a list_item div class
        episodes_html = soup_season.find_all(attrs={'class':'list_item'})

        season_number = soup_season.find(attrs={'id':'episode_top'}).get_text().replace(u'eason\xa0', u'')
        total_episodes = soup_season.find(attrs={'itemprop':'numberofEpisodes'})['content']


        # All episodes are stored inside a array
        episodes_info = []
        for epi in episodes_html:
            episodes_info.append(self.scrap_episode(epi,season_number))
        season_info = {
            'season_text':season_number,
            'total_episodes':total_episodes,
            'episodes':episodes_info
            }
        return season_info

    def scrap_show_dict(self):
        divs = self.soup_show.find(attrs={'class':'seasons-and-year-nav'}).find_all('div')
        links = divs[2].find_all('a')
        self.links_seasons = [IMDB_URL  + link.get('href') for link in links]
        self.title = self.soup_show.find('title').get_text()
        self.storyline = self.soup_show.find(attrs={'class':'inline canwrap'}).get_text() 
        print(self.title)
        print(self.storyline)
        self.show = {
            'url':self.url,
            'title':self.title,
            'storyline':self.storyline,
        }
        for season_link in self.links_seasons:
            season_info = self.scrap_season_dict(season_link)
            self.show[season_info['season_text']] = season_info
    
    def scrap_show_array(self):
        divs = self.soup_show.find(attrs={'class':'seasons-and-year-nav'}).find_all('div')
        links = divs[2].find_all('a')
        self.links_seasons = [IMDB_URL  + link.get('href') for link in links]
        self.title = self.soup_show.find('title').get_text()
        self.storyline = self.soup_show.find(attrs={'class':'inline canwrap'}).get_text() 
        print(self.title)
        print(self.storyline)
        seasons = []
        for season_link in self.links_seasons:
            seasons.append(self.scrap_season_array(season_link))
        self.show = {
            'url':self.url,
            'title':self.title,
            'storyline':self.storyline,
            'seasons':seasons
        } 

    def get_title(self):
        return self.title
    
    def get_url(self):
        return self.url
    
    def get_json(self):
        return self.show

    def save_json(self):
        with open('shows/'+self.title+'.json', 'w') as fp:
            json.dump(self.show, fp)
        print("Saved")
   
    def get_dataframe(self):
        # d = json_normalize(self.show['seasons'])
        works_data = json_normalize(data=self.show['seasons'], record_path='episodes')
        return works_data
    def plot(self):
        df = self.get_dataframe()
        df = df.sort_values(['info.season','episode_number'])
        ax = df.plot(x='info.short',y='info.rating')
        ax.set_xticks(range(len(df['info.short']))) 
        ax.set_xticklabels([item for item in df['info.short'].tolist()],rotation=0)
