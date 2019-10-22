import requests
from bs4 import BeautifulSoup
import re


IMDB_URL = 'https://www.imdb.com'


# Some chars that need to be removed in text (air_date)
REMOVE_CHARS = ['\n','\t','\s+']
rx = '[' + re.escape(''.join(REMOVE_CHARS)) + ']'

class imdb:
    def __init__(self,url):
        self.url = url
        self.soup_show = self.make_request(url)
        self.scrap_show()

    def make_request(self,url):
        response = requests.get(url)
        if response.status_code == 200:
            print('Successful Request at: ', url)
            soup  = BeautifulSoup(response.content,'html.parser')
            return soup
        elif response.status_code == 404:
            print('Not Found.')

    def update_title(self):
        self.title = self.soup_show.find('title').get_text()  
        self.general_rating = self.soup_show.find(attrs={'itemprop':'ratingValue'}).get_text()
    
    
    def update_seasons(self):
        divs = self.soup_show.find(attrs={'class':'seasons-and-year-nav'}).find_all('div')
        links = divs[2].find_all('a')
        self.links_seasons = [IMDB_URL  + link.get('href') for link in links]


    def get_ratings(self):
        self.season_rating = {}
        for link_season in self.links_seasons:
            print(link_season)
            soup_season = self.make_request(link_season)

            episodes_html = soup_season.find_all(attrs={'class':'list_item'})
            season_number = soup_season.find(attrs={'id':'episode_top'}).get_text()
            total_episodes = soup_season.find(attrs={'itemprop':'numberofEpisodes'})['content']

            ratings ={}
            for epi in episodes_html:
                # scrap_episode(epi)
                info = epi.find(attrs={'class':'info'})
                air_date = re.sub(rx,' ',info.find(attrs={'class':'airdate'}).get_text()).strip()
                rating = info.find(attrs={'class':'ipl-rating-star__rating'}).get_text()
                episode_number = info.find(attrs={'itemprop':'episodeNumber'})['content']
                print(rating,episode_number,air_date.replace('\n',''))
                ratings[episode_number] = {'air_data':air_date, 'rating':rating}
            self.season_rating[season_number] = {'total_episodes':total_episodes, 'ratings' : ratings}
    
    def scrap_episode(self,epi_tag):
        
        info = epi_tag.find(attrs={'class':'info'})
        
        # get some info of the episode, can be improved and get more if necessary
        air_date = re.sub(rx,' ',info.find(attrs={'class':'airdate'}).get_text()).strip()
        rating = info.find(attrs={'class':'ipl-rating-star__rating'}).get_text()
        total_votes = info.find(attrs={'class':'ipl-rating-star__total-votes'}).get_text()
        episode_number = info.find(attrs={'itemprop':'episodeNumber'})['content']
        episode_description = info.find(attrs={'itemprop':'description'}).get_text()
        episode_title = info.find(attrs={'itemprop':'name'}).get_text()
        episode_info = {
            'number': episode_number,

            'info':{
                'rating': rating,
                'total_votes': total_votes,
                'air_date': air_date,
                'description': episode_description,
                'episode_title': episode_title
                
            }

            }
        # print(episode_info)
        return episode_info

    def scrap_season(self,season_url):
        soup_season = self.make_request(season_url)

        # the list of all episodes in imdb page are in a list_item div class
        episodes_html = soup_season.find_all(attrs={'class':'list_item'})

        season_number = soup_season.find(attrs={'id':'episode_top'}).get_text()
        total_episodes = soup_season.find(attrs={'itemprop':'numberofEpisodes'})['content']

        episodes_info = []
        for epi in episodes_html:
            episodes_info.append(self.scrap_episode(epi))
        season_info = {
            'season_text':season_number,
            'total_episodes':total_episodes,
            'episodes_info':episodes_info
            }
        return season_info
    # def scrap_season(self,season_url):
    #     soup_season = self.make_request(season_url)

    #     # the list of all episodes in imdb page are in a list_item div class
    #     episodes_html = soup_season.find_all(attrs={'class':'list_item'})

    #     season_number = soup_season.find(attrs={'id':'episode_top'}).get_text()
    #     total_episodes = soup_season.find(attrs={'itemprop':'numberofEpisodes'})['content']
    #     season_info = {
    #         'season_text':season_number,
    #         'total_episodes':total_episodes,
    #         }
        
    #     for epi in episodes_html:
    #         season_info['episodes'] = self.scrap_episode(epi)
    #     return season_info



    def scrap_show(self):
        divs = self.soup_show.find(attrs={'class':'seasons-and-year-nav'}).find_all('div')
        links = divs[2].find_all('a')
        self.links_seasons = [IMDB_URL  + link.get('href') for link in links]
        self.title = self.soup_show.find('title').get_text()
        print(self.title)

        self.show = {
            'url':self.url,
            'title':self.title,
        }
        for season_link in self.links_seasons:
            season_number = season_link.split('=')[-1]
            self.show[season_number] =self.scrap_season(season_link) 
    def get_title(self):
        return self.title
    def get_url(self):
        return self.url
    def get_show(self):
        return self.show

