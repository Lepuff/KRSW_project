

from typing import List
import stardog
import re
from datetime import date
import musicbrainzngs
#General stuff
musicbrainzngs.set_useragent("KSRW_project","1.0",contact=None)
musicbrainzngs.set_hostname("musicbrainz.org",use_https=False)

def browse_rel(artist_mbid,limit,offset):
  return musicbrainzngs.browse_releases(artist=artist_mbid,
                                        release_type=["album","single"],release_status=["official"],
                                        includes=["media"], limit=limit, offset=offset)



def getReleasesByMbID(artist_mbid):
  limit = 100
  offset = 0
  releases = []
  page = 1
  result = browse_rel(artist_mbid,limit,offset)
  page_releases = result['release-list']
  releases += page_releases
  while len(page_releases) >= limit:
    offset += limit
    page += 1
    result = browse_rel(artist_mbid,limit,offset)
    page_releases = result['release-list']
    releases += page_releases

  releases_list =[]
  u_list = []
  for r in releases:
    trackcount = 0
    id =""
    title =""
    date =""
    if "title" in r:
      title = r["title"]
    if "id" in r:
      id = r["id"]
    if "date" in r:
      date = r["date"]
    if "medium-list" in r:
      trackcount = r["medium-list"][0]["track-count"]
    if r["title"] not in u_list:
      u_list.append(r["title"])
      releases_list.append((id,title,trackcount,date))
  return releases_list



#connect to the DBpedia endpoint 
conn_details = {
  'endpoint': 'https://dbpedia.org/'
}

#name of the datbase to query
db = "sparql"
lang = "en"

#connect to the database
with stardog.Connection(db, **conn_details) as conn:
    #query
    #####update the query as needed 
  name = input("SAY MY NAME:\n")
  results = conn.select("""
  select distinct *
  where 
  {
    ?artist foaf:name ?name ;
            owl:sameAs ?musicBrainz ;
            dbo:activeYearsStartYear ?startYear ;
            dbo:abstract ?about .

      optional {  ?artist dbo:birthDate ?birthDate .
                  ?artist dbo:birthYear ?birthYear . }
      optional {  ?artist dbo:deathDate ?deathDate . 
                  ?artist dbo:deathYear ?deathYear .}
      optional {  ?artist dbo:activeYearsEndYear ?endYear .}
    """
    f"""
    filter langMatches(lang(?about),'{lang}')
    filter regex(?musicBrainz, "musicbrainz") .
    """
    f"""filter regex(?name, "{name}"@{lang}) . """    
    """
    } limit 1
    """
      )
#The SPARQL query result is serialized in a JSON format. 
#The format details can be found at https://www.w3.org/TR/sparql11-results-json/
# 

for result in results["results"]["bindings"]:
  #myList.append(result["name"]["value"])
  musicbrainzID = re.split(r'http://musicbrainz.org/artist/', result["musicBrainz"]["value"])
  about = result["about"]["value"]
  name = result["name"]["value"]
  print('Name is:', name)
  age = date.today().year

  if("birthDate" in result):
    birthDate = result["birthDate"]["value"]
    print('Birth date is:', birthDate)
    birthYear = int(result["birthYear"]["value"])
    if ("deathDate" in result):
      deathDate = result["deathDate"]["value"]
      print('Date of death is:', deathDate)
      age = int(result["deathYear"]["value"])
    age -= birthYear
    print(f"Age: {age} years old")

    startYear = int(result["startYear"]["value"])
    print('Start year is:', startYear)

    yearsActive = int(date.today().year) - startYear
    if ("endYear" in result):
      endYear = int(result["endYear"]["value"])
      print("End year is:", endYear)
      yearsActive = endYear-startYear
    print('Years active:', yearsActive)
    #print(about)
    #print('years active:', (int(date.year())-int(result["startYear"]["value"])))

# musicbrainzID is split using regex, which is why the ID is [1]
releases_list = getReleasesByMbID(musicbrainzID[1])
for rel in releases_list:
  print(rel)

