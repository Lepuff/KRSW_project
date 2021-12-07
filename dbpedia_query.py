

from typing import List
import stardog
import re
from datetime import date
import musicbrainzngs
#General stuff
musicbrainzngs.set_useragent("KSRW_project","1.0",contact=None)
musicbrainzngs.set_hostname("musicbrainz.org",use_https=False)


def getReleasesByMbID(artist_mbid):
  #label = "71247f6b-fd24-4a56-89a2-23512f006f0c"
  #label ="b95ce3ff-3d05-4e87-9e01-c97b66af13d4"
  limit = 100
  offset = 0
  releases = []
  page = 1
  #print("fetching page number %d.." % page)
  result = musicbrainzngs.browse_releases(artist=artist_mbid,
                                          release_type=["album","single"],release_status=["official"],
                                          includes=["media"], limit=limit, offset=offset)
  page_releases = result['release-list']
  releases += page_releases
  # release-count is only available starting with musicbrainzngs 0.5
  if "release-count" in result:
    count = result['release-count']
    

    while len(page_releases) >= limit:
      offset += limit
      page += 1
      # print("fetching page number %d.." % page)
      result = musicbrainzngs.browse_releases(artist=artist_mbid,
                                              release_type=["album","single"],
                                              release_status=["official"],includes=["media"], 
                                              limit=limit, offset=offset)
      page_releases = result['release-list']
      releases += page_releases

    releases_list =[]
    u_list = []
    for r in releases:
      trackcount = r["medium-list"][0]["track-count"] 
      #print("id : "+r["id"]+"   title: "+r["title"] + " track count : "+str(trackcount))
      if r["title"] not in u_list:
        u_list.append(r["title"])
        releases_list.append((r["id"],r["title"],trackcount))#r["date"],trackcount))
    return releases_list



#connect to the DBpedia endpoint 
conn_details = {
  'endpoint': 'https://dbpedia.org/'
}

#name of the datbase to query
db = "sparql"


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
      optional { ?artist dbo:activeYearsEndYear ?endYear .}

      optional {  ?artist dbo:birthDate ?birthDate .
                  ?artist dbo:birthYear ?birthYear .
                  ?artist dbo:deathDate ?deathDate . 
                  ?artist dbo:deathYear ?deathYear .}
    """
    """
    filter langMatches(lang(?about),'en')
    filter regex(?musicBrainz, "musicbrainz") .
    """
    f"""filter regex(?name, "{name}"@en) . """    
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

