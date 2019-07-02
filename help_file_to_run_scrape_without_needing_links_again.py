import pandas as pd

links = pd.read_csv("movie_links.csv", usecols=["movie_links"])

print(type(links))
movie_links = list(links["movie_links"])

for link in movie_links[:50]:
    print(link)