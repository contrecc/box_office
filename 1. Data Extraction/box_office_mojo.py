############################################################
# STEP 1: IMPORT ALL NEEDED LIBRARIES
############################################################

# Import general libraries
import pandas as pd
import numpy as np
import random
import time
import re
from multiprocessing import Pool  
from multiprocessing import cpu_count
import os

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


# BeautifulSoup helper functions
def find_profession(soup_instance, profession_type_regex, how_many):
    # Create a list for how many results to find
    results_list = [None] * how_many
    
    # Search the soup for the regex
    search = soup_instance.find("a", href=re.compile(profession_type_regex))
    
    # Filter text if the search hits
    if search is not None:
        text_list = search.find_next("td").get_text(separator=",", strip=True).replace("*", "").split(",")
        
        # Fix ", Jr." problem for names after splitting the text_list
        filtered_list = combine_jrs(text_list)
        
        # Remove things like '(executive producer)' from the text_list
        filtered_list = remove_titles_from_list(filtered_list)
          
        len_filtered_list = len(filtered_list)
        
        # Assign results to results_list and then assign the rest to be "N/A" 
        for i in range(how_many):
            if i < len_filtered_list:
                results_list[i] = filtered_list[i]
            else:
                results_list[i] = "N/A"
    else:
        results_list = ["N/A"] * how_many
    
    if how_many == 1:
        return results_list[0]
    else:
        return results_list

def combine_jrs(names_list):
    new_list = []
    temp_name = ""
    
    for i in range(len(names_list)):
        if names_list[i] != " Jr.":
            
            if temp_name == "":
                temp_name = names_list[i]
            else:
                new_list.append(temp_name)
                temp_name = names_list[i]
                
            if i == len(names_list) - 1:
                new_list.append(temp_name)
                
        elif names_list[i] == " Jr.":
            temp_name = "{},{}".format(temp_name, names_list[i])
            new_list.append(temp_name)
            temp_name = ""
            
    return new_list

def remove_titles_from_list(names_list):
    new_list = []
    
    for name in names_list:
        if re.search(r"^\(.+\)$", name, re.IGNORECASE):
            continue
        else:
            new_list.append(name)
    return new_list

def find_box_office(soup_instance, box_office_type):
    box_office = soup_instance.find("div", {"class": "mp_box_content"})
    
    if box_office is not None:
        trs = box_office.findAll("tr")

        for tr in trs:
            tr_text = tr.get_text()
            match_test = re.search(box_office_type, tr_text, re.IGNORECASE)

            if match_test is not None:
                filtered_result = re.search(r"\$[0-9,]+", tr_text)

                if filtered_result is not None:
                    return filtered_result[0]
                else:
                    return "N/A"
    return "N/A"

def find_items_by_bold_tag(soup_instance):
    bs = soup_instance.findAll("b")

    try:
        title = bs[1].get_text(strip=True) or "N/A"
    except Exception:
        title = "N/A"

    # Check if "Domestic Total Gross" or "Domestic Lifetime Gross" are present
    # For each one present, the search items are located one bold tag deeper in the soup
    try:
        domestic_total_gross_check = "$" in bs[2].get_text(strip=True)
    except Exception:
        domestic_total_gross_check = False

    try:
        domestic_lifetime_gross_check = "$" in bs[3].get_text(strip=True)
    except Exception:
        domestic_lifetime_gross_check = False

    offset_sum = domestic_total_gross_check + domestic_lifetime_gross_check
    
    # Our urls will adjust the `Domestic Total Gross` to 2019 dollars (by adding the `&adjust_yr=2019&p=.htm` parameter)
    # We only return `Adjusted Domestic Gross 2019` if the `Domestic Total Gross` is present
    if domestic_total_gross_check:
        try:
            adjusted_domestic_gross_2019 = bs[2].get_text(strip=True) or "N/A"
        except Exception:
            adjusted_domestic_gross_2019 = "N/A"
    else:
        adjusted_domestic_gross_2019 = "N/A"
    
    try:
        distributor = bs[2 + offset_sum].get_text(strip=True) or "N/A"
    except Exception:
        distributor = "N/A"

    try:
        release_date = bs[3 + offset_sum].get_text(strip=True) or "N/A"
    except Exception:
        release_date = "N/A"

    try:
        genres = bs[4 + offset_sum].get_text(strip=True) or "N/A"
    except Exception:
        genres = "N/A"

    try:
        runtime = bs[5 + offset_sum].get_text(strip=True) or "N/A"
    except Exception:
        runtime = "N/A"

    try:
        rating = bs[6 + offset_sum].get_text(strip=True) or "N/A"
    except Exception:
        rating = "N/A"
    
    try:
        production_budget = bs[7 + offset_sum].get_text(strip=True) or "N/A"
    except Exception:
        production_budget = "N/A"
    
    return [title, adjusted_domestic_gross_2019, distributor, release_date, genres, runtime, rating, production_budget]

# Function to scrape a url and extract all movie data from it
def scrapeWebsite(url):
    try:
        # Fix an encoding error with these movies' urls
        if "elizabeth" in url and "elizabethtown" not in url:
            url="http://www.boxofficemojo.com/movies/?id=elizabeth%A0.htm&adjust_yr=2019&p=.htm"

        if "simpleplan" in url:
            url="http://www.boxofficemojo.com/movies/?id=simpleplan%A0.htm&adjust_yr=2019&p=.htm"

        # Fetch the movie page
        try:
            response = requests_retry_session().get(url)
        except Exception:
            return 0

        soup = BeautifulSoup(response.text, "html.parser")

        # Sleep to prevent fetching too many pages at once
        time.sleep(1)

        try:
            director1, director2 = find_profession(soup, "Director&", 2)
        except Exception:
            director1, director2 = ["N/A"] * 2

        try:
            writer1, writer2, writer3 = find_profession(soup, "Writer&", 3)
        except Exception:
             writer1, writer2, writer3 = ["N/A"] * 3

        try:
            actor1, actor2, actor3, actor4, actor5, actor6 = find_profession(soup, "Actor&", 6)
        except Exception:
            actor1, actor2, actor3, actor4, actor5, actor6 = ["N/A"] * 6

        try:
            producer1, producer2, producer3, producer4, producer5, producer6 = find_profession(soup, "Producer&", 6)
        except Exception:
            producer1, producer2, producer3, producer4, producer5, producer6 = ["N/A"] * 6

        try:
            composer1, composer2 = find_profession(soup, "Composer&", 2)
        except Exception:
            composer1, composer2 = ["N/A"] * 2

        try:
            cinematographer = find_profession(soup, "Cinematographer&", 1)
        except Exception:
            cinematographer = "N/A"

        try:
            title, adjusted_domestic_gross_2019, distributor, release_date, genres, runtime, rating, production_budget = find_items_by_bold_tag(soup)
        except Exception:
            title, adjusted_domestic_gross_2019, distributor, release_date, genres, runtime, rating, production_budget = ["N/A"] * 8

        try:
            domestic_gross = find_box_office(soup, "Domestic") 
        except Exception:
            domestic_gross = "N/A"

        try:
            foreign_gross = find_box_office(soup, "Foreign")
        except Exception:
            foreign_gross = "N/A"

        try:
            worldwide_gross = find_box_office(soup, "Worldwide")
        except Exception:
            worldwide_gross = "N/A"
            
    except Exception:
        return 0
    
    return [title, distributor, runtime, rating, release_date, genres, domestic_gross, foreign_gross, worldwide_gross, adjusted_domestic_gross_2019, production_budget, director1, director2, writer1, writer2, writer3, actor1, actor2, actor3, actor4, actor5, actor6, producer1, producer2, producer3, producer4, producer5, producer6, cinematographer, composer1, composer2]

# Function to convert runtime from `1 hrs. 30min.` format to an integer of total minutes
def convert_runtime_to_integer(runtime):
    if pd.isna(runtime):
        return np.nan
    
    if "hrs." not in runtime:
        return np.nan
    
    runtime_split = runtime.split(" ")
    
    hrs = int(runtime_split[0]) * 60
    mins = int(runtime_split[2])
    
    return hrs + mins 

# Function to clear the console between print statements
def clear():
    os.system("cls")

#############################################################
# STEP 3: MAIN PROGRAM
#############################################################

if __name__ == "__main__":
    # Initiate empty list to store all movie links
    movie_links = []

    # Base url to find all movie pages from
    url = "https://www.boxofficemojo.com/movies/alphabetical.htm"

    try:
        t0 = time.time()
        response = requests_retry_session().get(url)
    except Exception as e:
        print("Initial URL fetch failed", e.__class__.__name__)
    else:
        print("Initial URL fetch eventually worked", response.status_code)
    finally:
        t1 = time.time()
        print("Initial fetch took", t1 - t0, "seconds")
        
    soup = BeautifulSoup(response.text, "html.parser")

    # Find links to all letters of the alphabet that movies can start with (e.g. A, B, C, #)
    letters = soup.findAll("a", href=re.compile("letter="))

    # Remove duplicates from second navbar with the same information
    unique_letters = list(set(letters))

    # Create a list to store the links to each individual letter
    letters_list = []

    for letter in unique_letters:
        letters_list.append("https://www.boxofficemojo.com{}".format(letter["href"]))
        
    for letter in letters_list:
        print(letter)

    # Save the list of letters links 
    letters_list_df = pd.DataFrame({"letters_list": letters_list})
    letters_list_df.to_csv("letters_list.csv", index=False)

    # Now go through each letter and find all movies associated with it
    for i in range(0,27):
        current_url = letters_list[i]
        time.sleep(1)
        clear()
        
        try:
            t0 = time.time()
            response = requests_retry_session().get(current_url)
        except Exception as e:
            print("Fetching {} failed".format(current_url), e.__class__.__name__)
        else:
            print("Fetching {} eventually worked".format(current_url), response.status_code)
        finally:
            t1 = time.time()
            print("Fetching {} took".format(current_url), t1 - t0, "seconds")

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all movie links on this page (the links are within <tr> tags)
        trs = soup.findAll("tr")
        
        # Append all movie links to the list and adjust all dollar amounts to year 2019 for analysis purposes    
        for tr in trs:
            found_links = tr.findAll("a", href=re.compile("id="))
            for link in found_links:
                movie_links.append("https://boxofficemojo.com{}{}".format(link["href"], "&adjust_yr=2019&p=.htm"))
        
        # Find if there are other pages for this letter (e.g. A-Ab, Ac-Ad)
        navbar = soup.find("div", "alpha-nav-holder")
        pages = navbar.findAll("a", href=re.compile("letter="))
        
        # Initiate an empty pages_list for each letter
        pages_list = []
        
        for page in pages:
            pages_list.append("https://www.boxofficemojo.com{}{}".format(page["href"], "&adjust_yr=2019&p=.htm"))
            
        if len(pages_list) > 0:
            for page in pages_list:
                time.sleep(1)
                
                try:
                    t0 = time.time()
                    response = requests_retry_session().get(page)
                except Exception as e:
                    print("Fetching {} failed".format(page), e.__class__.__name__)
                else:
                    print("Fetching {} eventually worked".format(page), response.status_code)
                finally:
                    t1 = time.time()
                    print("Fetching {} took".format(page), t1 - t0, "seconds")
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                trs = soup.findAll("tr")
                
                for tr in trs:
                    found_links = tr.findAll("a", href=re.compile("id="))
                    for link in found_links:
                        movie_links.append("https://boxofficemojo.com{}{}".format(link["href"], "&adjust_yr=2019&p=.htm"))
                        
        print("Number of movie links:", len(movie_links))
    print("Movie links scraping finished!") 
    print("Total number of movie links:", len(movie_links))

    # Save the list of movie links 
    movie_links_df = pd.DataFrame({"movie_links": movie_links})
    movie_links_df.to_csv("movie_links.csv", index=False)

    ############################################################
    # STEP 4: USE THREADS TO SPEED UP WEBSCRAPING
    ############################################################

    print("Starting scrape")

    # Set up threads to speed up web-scraping
    pool = Pool(cpu_count() * 2)  
    results = pool.map(scrapeWebsite, movie_links)
    pool.close()
    pool.join()

    print("Scrape finished")

    ############################################################
    # STEP 5: PRELIMINARY CLEANUP
    ############################################################

    # Eliminate bad records
    results = [result for result in results if result is not 0]

    # Store the results in a DataFrame
    movie_data = pd.DataFrame.from_records(results, columns=["title", "distributor", "runtime", "rating", "release_date", "genres", "domestic_gross", "foreign_gross", "worldwide_gross", "adjusted_domestic_gross_2019", "production_budget", "director1", "director2", "writer1", "writer2", "writer3", "actor1", "actor2", "actor3", "actor4", "actor5", "actor6", "producer1", "producer2", "producer3", "producer4", "producer5", "producer6", "cinematographer", "composer1", "composer2"])

    # Preliminary data cleanup -- converting appropriate data to numeric or datetime type
    movie_data["domestic_gross_formatted"] = movie_data["domestic_gross"].str.replace(",", "").str.replace("$", "")
    movie_data["domestic_gross_formatted"] = pd.to_numeric(movie_data["domestic_gross_formatted"], errors="coerce")

    movie_data["foreign_gross_formatted"] = movie_data["foreign_gross"].str.replace(",", "").str.replace("$", "")
    movie_data["foreign_gross_formatted"] = pd.to_numeric(movie_data["foreign_gross_formatted"], errors="coerce")

    movie_data["worldwide_gross_formatted"] = movie_data["worldwide_gross"].str.replace(",", "").str.replace("$", "")
    movie_data["worldwide_gross_formatted"] = pd.to_numeric(movie_data["worldwide_gross_formatted"], errors="coerce")

    movie_data["adjusted_domestic_gross_2019_formatted"] = movie_data["adjusted_domestic_gross_2019"].str.replace(",", "").str.replace("$", "")
    movie_data["adjusted_domestic_gross_2019_formatted"] = pd.to_numeric(movie_data["adjusted_domestic_gross_2019_formatted"], errors="coerce")

    # movie_data["production_budget_formatted"] = movie_data["production_budget"].str.replace(",", "").str.replace("$", "")
    # movie_data["production_budget_formatted"] = pd.to_numeric(movie_data["production_budget"], errors="coerce")

    movie_data["release_date_formatted"] = pd.to_datetime(movie_data["release_date"], errors="coerce")

    movie_data["runtime_formatted"] = movie_data["runtime"].apply(lambda x:convert_runtime_to_integer(x))

    ############################################################
    # STEP 6: SAVE SCRAPED DATA FOR FURTHER ANALYSIS
    ############################################################

    # Save movie_data as a pickle
    movie_data.to_pickle("movie_data.pkl")

    # Save movie_data as a CSV
    movie_data.to_csv("movie_data.csv", index=False)

    print("Files written!")
