# Da Best Movie Genre?! 

We work for a Big 5 movie studio, and they've asked us to pick the best movie genre to invest in. 

Our gut tells us the right answer is just whatever movie Dwayne Johnson wants to make.

But I guess we can look at data.

This project can be subdivided into four steps (as of this moment):

## Step 1 -- Find and source movie data

While researching good sources of movie data, I found two websites: [The Numbers](https://www.the-numbers.com/) and [Box Office Mojo](https://www.boxofficemojo.com/). 
Both of these have a wealth of information about movies, such as production budget, genre, domestic box office, and worldwide box office

I found a [useful scraping script](https://github.com/csredino/Box-Office-Mojo-Scrapper/blob/master/movie_data.csv) for Box Office Mojo and modified it to account for recent changes in the website. I also wrote a separate scraping script for The Numbers.

These scripts are `box_office_mojo.py` and `the_numbers.py`.

They first collect all the URLs from Box Office Mojo and The Numbers that have information about individual movies.

Then, using the `multiprocessing` module in Python, I spread the work of scraping the links to several processes to speed up the script.

The type of data I collected from each website includes the following:
  - Box Office Mojo - title, distributor, runtime, rating, release_date, genres, domestic_gross, foreign_gross, worldwide_gross, adjusted_domestic_gross_2019, production_budget, director1, director2, writer1, writer2, writer3, actor1, actor2, actor3, actor4, actor5, actor6, producer1, producer2, producer3, producer4, producer5, producer6, cinematographer, composer1, composer2
  - The Numbers - rank (from highest to lowest production budget), release_date, title, production_budget, domestic_gross, worldwide_gross

I performed some initial data cleanup, such as converting numeric data stored as strings into numeric data types, then saved the data to csv files: `the_numbers_movie_data.csv` and `movie_data.csv`.

## Step 2 -- Data cleaning

The bulk of the data cleaning was performed in the `Data_Cleaning.ipynb` notebook. 

The steps include:

1) Importing the two datasets and finishing up any datatype conversions.

2) Performing an outer merge on `title` and `release_year` to consolidate duplicate entries.

3) Combining duplicate entries that have different release years. Since a movie's release date can vary by country, we can have the same movie with a release date of December 2009 and February 2010. We loop through our dataframe and combine entries that have consecutive release years and matching titles to account for this.

4) Consolidating redundant columns.
  - If Box Office Mojo and The Numbers both have a release date for the same movie, we keep the one from Box Office Mojo.
  - If Box Office Mojo and The Numbers both have production budgets, domestic grosses, or worldwide grosses for the same movie, we take the average value.

5) Adjusting for inflation. Our two datasets contain movies from the 1910s to the 2010s. The numerical data is not adjusted for inflation. Since we want to compare the relative success of movies by genre, we try two methods of normalizing our monetary data to 2018 dollars:
  - We found the average ticket price for each year in our dataset. We then convert all movies to 2018 dollars by dividing by that year's ticket price and multiplying by the 2018 ticket price amount in dollars. 
  - We found the python package `cpi` which uses the Consumer Price Index to convert dollars from any year to 2018 dollars.
  
We compared the results of both conversions. Using the CPI method resulted in less extreme values over time. For example, in looking at Gone With The Wind with the CPI method, the domestic gross in 2018 dollars is $3.6 billion dollars. Using the ticket price conversion method, we get a domestic gross in 2018 dollars of $7.9 billion. Gone With The Wind was the biggest movie of all time, but given that neither Avatar nor Avengers: Endgame grossed $3 billion, the lower amount seems like a better conversion.  
  
6) Creating a `release_week` column.

7) Rename some columns to simplify further analysis

8) Saving the output to `cleaned_movie_data.csv`.

## Step 3 -- Data Analysis -- Domestic Movies

In the `Domestic.ipynb` notebook, we analyze the domestic box office performance of movies, grouped into one of six main genres: Action, Adventure, Comedy, Drama, Horror, and Thriller/Suspense. Obviously, there are more genres, but if we don't simplify it, we run the risk of getting lost in genre soup.

We only look at movies released by the Big 5 studios (Universal, Disney, Paramount, Sony, and Warner Bros.) to prevent lack of budget or marketing affecting a movie's chance of success. All movies can fail, but one from a major studio has the best leg up, so to speak.

We analyze performance by looking at domestic box office, production budget, and breakeven percentage. We look at these areas by decade as well as release week.

We find that from a cost-conscious perspective, Horror is the best genre. It has one of the cheapest production budgets and one of the highest chances to make money (i.e. at least break even).

We find that from an reward-based outlier perspective (i.e. making the most money per movie), Action and Adventure movies fare the best.

The genres least affected by release week are Comedy and Drama. If the studio is worried about fighting for prime release weeks, these genres are the easiest to plug and play throughout the year.

## Step 4 -- Data Analysis -- Worldwide Movies

In the `Worldwide.ipynb` notebook, we analyze the worldwide box office performance of movies, again grouped into one of the six main genres.

The inclusion of the rest of the world's money doesn't change much in terms of our recommendations to our bosses.

Horror, Action, and Adventure still fare the best on the global stage.

Horror is still the safest from a break even perspective. It also has the lowest median production budget of all genres, and the third highest median worldwide gross of $110 million, behind only Action's $324 million and Adventure's $419 million.

Action and Adventure are the second and third safest genres from a break even perspective. They are also the only two genres whose median gross has more than doubled since the 2000s. Their biggest downside is their much higher production budgets (Action: $115 million, Adventure $172 million -- next closest genre is Thriller/Suspense with $35 million).

Our recommendations to our bosses would be to make Horror movies if capital is an issue, and Action/Adventure if not. The other genres haven't been performing well in the last decade.

## Next Steps

Note that we only have box office information, whereas movies make money from a variety of release windows these days. Next steps would be incorporating such data to see how the relative success of these genres changes.

We could also analyze movies by other factors, such as by distributor or key talent (actor, director, writer, etc.).

Or we could simplify our lives and just fund movies with The Rock in them.
