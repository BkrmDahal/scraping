import re
import requests
from collections import defaultdict

from bs4 import BeautifulSoup
from nltk.corpus import stopwords

#get company from connection
connections = pd.read_csv('Connections.csv')

#text cleaning for company name
cachedStopWords = stopwords.words("english")
def text_cleaning(x, cachedStopWords=cachedStopWords):
    """Clean text: remove non alphabetical words, stopwords and duplicate words"""
    x = re.sub(r'[-\\/()]', ' ', x)
    x = re.sub(r'[^a-zA-Z ]', '', x)
    x = x.lower()
    word_list =[]
    
    # make copy of stopwords
    words = list(cachedStopWords)
    for word in x.encode('utf-8').split():
        if word not in words:
            if word[-1]=='s':
                word = word[:-1]
                word = word.decode('utf-8')
                #word = word[1:]
                word_list.append(word)
                words += [word]
            else:
                word = word.decode('utf-8')
                #word = word[1:]
                word_list.append(word)
                words += [word]
    
    return ' '.join(word_list)

##clean the test
connections['Company'] = connections['Company'].map(str).map(lambda x: text_cleaning(x))

#get country code of all country
def country_code(i):
    """Get country code from url"""
    _cc = i.split('.')
    if _cc[-1] == 'com/':
        cc = _cc[0][-2:]
    else:
        cc = _cc[-1][:2]
    return cc

def country_url():
    """Get list of all countries with url"""
    r = requests.get('https://www.indeed.com/worldwide')
    soup = BeautifulSoup(r.content, 'lxml')
    countries = soup.find(attrs ={'class':'countries'}).find_all('a')
    
    country_list  = {}
    for i, country in enumerate(countries):
        temp ={}
        if np.mod(i,2) == 1:
            country_link = country.get('href')
            temp['url'] = country_link
            try:
                temp['country'] = country.get_text()
            except:
                temp['country'] = None
                
            country_list[country_code(country_link)] = temp
            
    return country_list

#class for getting all job listing
class jobListing():
    def __init__(self, country_code = 'in'):
        self.all_url = country_url()
        self.url = self.all_url[country_code]['url']+'jobs/'
        self.headers = {'User-Agent':  """Mozilla/5.0"""}
        self.detail = defaultdict(list)
        
    def get_soups(self, as_and = '',as_ttl = '', as_cmp = '',
                salary = '',l = '', start=0, limit=50, **kwargs ):
        """Get html of jobs page
        Params
        -------
        as_and: search query can be company number or title or any word in description
        as_ttl: search only if present in title
        as_cmp: company name
        salary: Rs90000 will search Rs90000+ or Rs40K-Rs50K
        l: location
        start: start of search label detail
        limit: no of job posting to display
        kwargs: https://www.indeed.co.in/advanced_search
            as_and=&as_phr=&as_any=&as_not=&as_ttl=&as_cmp=&
            jt=all&st=&salary=&radius=25&l=&fromage=any&
            limit=10&sort=&psf=advsrch"""
        
        params = locals()
        params.pop('self', None)
        
        if 'kwargs' in params.keys():
            params.pop('kwargs',None)
            self.params = {**params, **kwargs}
            
        self.params_list = ''
        for i, j in self.params.items():
            if j !='':
                self.params_list += i + ': ' + str(j) + ' | '
            
        r = requests.get(self.url, headers =self.headers, params=self.params )
        self.soup = BeautifulSoup(r.content, 'lxml')
        self.soup_posting = self.soup.find_all(attrs={'data-tn-component':'organicJob'})
        print(self.params_list)
        print(r.url)
    
    @staticmethod
    def _get_number(x, get_last = False):
        x = re.findall(r'\d+', x)
        if get_last:
            return int(''.join(x[2:]))

        else:
            return int(x[0])
    
    def total_jobs(self):
        job_number = self.soup.find(attrs= {'id':'searchCount'}).get_text().strip()
        no_jobs = self._get_number(job_number, get_last = True)
        print("Total jobs found {}.".format(no_jobs))
        if no_jobs>1000:
            no_jobs = 1000

        self.pages = [i for i in range(0, no_jobs, 50)]
        
    def get_jobs(self):
        for job in self.soup_posting:
            self.detail['title'].append(job.find(attrs = {'class':'jobtitle'}).get_text().strip())
            self.detail['id'].append(job.find(attrs = {'class':'jobtitle'}).get('id'))
            self.detail['job_url'].append(job.find(attrs = {'class':'jobtitle'}).find('a').get('href'))
            self.detail['company'].append(job.find(attrs = {'class':'company'}).get_text().strip())
            try:
                self.detail['company_url'].append(job.find(attrs = {'class':'company'}).find('a').get('href'))
            except:
                self.detail['company_url'].append(None)
            try:
                ratings = job.find(attrs = {'class':'slNoUnderline'}).get_text().strip()
                self.detail['ratings'].append(self._get_number(ratings))
            except:
                self.detail['ratings'].append(None)

            self.detail['location'].append(job.find(attrs = {'itemprop':'addressLocality'}).get_text().strip())
            self.detail['summary'].append(job.find(attrs = {'class':'summary'}).get_text().strip())
            date = job.find(attrs = {'class':'date'}).get_text().strip()
            self.detail['date'].append(self._get_number(date))
            self.detail['query'].append(self.params_list)
            self.detail['company_q'].append(self.params['as_cmp'])
            
    def get_all_jobs(self, as_and = '',as_ttl = '', as_cmp = '',
                salary = '',l = '', start=0, limit=50, **kwargs):
        """Get all jobs
        Params
        -------
        as_and: search query can be company number or title or any word in description
        as_ttl: search only if present in title
        as_cmp: company name
        salary: Rs90000 will search Rs90000+ or Rs40K-Rs50K
        l: location
        start: start of search label detail
        limit: no of job posting to display
        kwargs: https://www.indeed.co.in/advanced_search
            as_and=&as_phr=&as_any=&as_not=&as_ttl=&as_cmp=&
            jt=all&st=&salary=&radius=25&l=&fromage=any&
            limit=10&sort=&psf=advsrch"""
        
        #get number of pages in result
        self.get_soups(as_and = as_and, as_ttl = as_ttl, as_cmp = as_cmp,
                salary = salary,l = l, start=0, limit=10)
        try:
            self.total_jobs()
            for i in self.pages:
                print("Started scraping...")
                self.get_soups(as_and = as_and, as_ttl = as_ttl, as_cmp = as_cmp,
                salary = salary,l = l, start=i, limit=50)
                self.get_jobs()
        except:
            print('No jobs in >>{}<<.\nTrying next item in list if any..\n '.format(self.params_list))
            
        
        #make detail as emptydict
        #self.detail = defaultdict(list)
        #return self.detail
        
##get all jobs of company in connection 
jobs_india =jobListing()
for i in set(connections['Company'][:10]):
    jobs_india.get_all_jobs(as_cmp=i)
df = pd.DataFrame(jobs_india.detail)

#save file
df = pd.DataFrame(jobs_india.detail)
df.to_excel('jobs_test.xlsx')