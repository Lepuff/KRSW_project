# 
# A simple example program for connecting and querying the Linked Data in Python.
#
# by  He Tan, 2021-10-14
#

from typing import List
import stardog
import json
import re
from datetime import date

"""
#connect to the local stardog triplestore server
conn_details = {
  'endpoint': 'http://localhost:5820',
  'username': 'admin',
  'password': 'admin'
}

#name of the datbase to query
db = "your_database"

"""

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

      OPTIONAL {  ?artist dbo:birthDate ?birthDate .
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
myList = []
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
  # print(test[1]) prints the musicbrainz id
