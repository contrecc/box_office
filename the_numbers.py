############################################################
# STEP 1: IMPORT ALL NEEDED LIBRARIES
############################################################

# Import general libraries
import pandas as pd
import time
from multiprocessing import Pool  
from multiprocessing import cpu_count

# Import BeautifulSoup for webscraping
from bs4 import BeautifulSoup

# Imports for `requests_retry_session` function
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

############################################################
# STEP 2: DEFINE ALL FUNCTIONS NEEDED
############################################################

# Use a custom wrapper to allow fetching with retries if failures happen
# https://www.peterbe.com/plog/best-practice-with-retries-with-requests
def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Scraping function
def scrapeWebsiteTheNumbers(url):
    try:
        response = requests_retry_session().get(url)
    except Exception:
        return 0

    # Through previous analysis, I learned the website is encoded with "ISO-8859-1".
    soup = BeautifulSoup(response.text, "lxml", from_encoding="iso-8859-1")

    # Sleep to prevent fetching too many pages at once
    time.sleep(1)

    # Create list to store all movies on a page
    page_data = []

    # Each page has only one table. By searching for all the <tr>s, we will get the data we need.
    # We do not need the first row of the table as this just has header information.
    for row in soup.find_all("tr")[1:]:
        columns = row.find_all("td")
        
        try:
            rank = columns[0].get_text()
        except Exception:
            rank = "N/A"
        
        try:
            release_date = columns[1].get_text().strip()
        except Exception:
            release_date = "N/A"
        
        # Some movie names has characters from foreign languages. We attempt to decode them into "utf-8" to account for this.
        # If there is a problem, we will use the text as is.
        try:
            title = columns[2].get_text().encode("ISO-8859-1", "ignore").decode("utf-8")
        except UnicodeDecodeError:
            title = columns[2].get_text()
        
        try:
            production_budget = columns[3].get_text()
        except Exception:
            production_budget = "N/A"
        
        try:
            domestic_gross = columns[4].get_text()
        except Exception:
            domestic_gross = "N/A"

        try:
            worldwide_gross = columns[5].get_text()
        except Exception:
            worldwide_gross = "N/A"

        page_data.append([rank, release_date, title, production_budget, domestic_gross, worldwide_gross])

    return page_data

#############################################################
# STEP 3: MAIN PROGRAM
#############################################################

if __name__ =="__main__":
    '''
    The URL addresses describe the entries by ranking.
    For example, /1 covers numbers 1 - 100. 
    /101 covers entries 101-200, etc.
    The last page in the list is /5701.
    ''' 
    pages = [str(i * 100 + 1) for i in range(58)]

    urls = ["https://www.the-numbers.com/movie/budgets/all/{}".format(page) for page in pages]

    ############################################################
    # STEP 4: USE THREADS TO SPEED UP WEBSCRAPING
    ############################################################

    print("Starting scrape")

    # Set up threads to speed up web-scraping
    pool = Pool(cpu_count() * 2)  
    results = pool.map(scrapeWebsiteTheNumbers, urls)
    pool.close()
    pool.join()

    print("Scrape finished")

    ############################################################
    # STEP 5: PRELIMINARY CLEANUP
    ############################################################

    # Flatten results to be a list of lists (not a list of list of lists)
    flattened_results = [item for sublist in results for item in sublist]

    # Eliminate bad records
    flattened_results = [result for result in flattened_results if result is not 0]

    # Store the results in a DataFrame
    movie_data = pd.DataFrame.from_records(flattened_results, columns=["rank", "release_date", "title", "production_budget", "domestic_gross", "worldwide_gross"])

    # Preliminary data cleanup -- converting appropriate data to numeric or datetime type
    movie_data["rank"] = pd.to_numeric(movie_data["rank"], errors="coerce")

    movie_data["release_date"] = pd.to_datetime(movie_data["release_date"], errors="coerce")

    movie_data["production_budget"] = movie_data["production_budget"].str.replace(",", "").str.replace("$", "")
    movie_data["production_budget"] = pd.to_numeric(movie_data["production_budget"], errors="coerce")

    movie_data["domestic_gross"] = movie_data["domestic_gross"].str.replace(",", "").str.replace("$", "")
    movie_data["domestic_gross"] = pd.to_numeric(movie_data["domestic_gross"], errors="coerce")

    movie_data["worldwide_gross"] = movie_data["worldwide_gross"].str.replace(",", "").str.replace("$", "")
    movie_data["worldwide_gross"] = pd.to_numeric(movie_data["worldwide_gross"], errors="coerce")

    ############################################################
    # STEP 6: SAVE SCRAPED DATA FOR FURTHER ANALYSIS
    ############################################################

    # Save movie_data as a pickle
    movie_data.to_pickle("the_numbers_movie_data.pkl")

    # Save movie_data as a CSV
    movie_data.to_csv("the_numbers_movie_data.csv", index=False)

    print("Files written!")