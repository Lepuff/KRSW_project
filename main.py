from queue import Empty
import PySimpleGUI as sg      
from typing import List
import requests
from requests.models import Response
import stardog
import re
from datetime import date
import musicbrainzngs
from io import BytesIO
import os
from PIL import Image
from PIL import ImageQt
import re
#General stuff
musicbrainzngs.set_useragent("KSRW_project","1.0",contact=None)
musicbrainzngs.set_hostname("musicbrainz.org",use_https=False)

#connect to the DBpedia endpoint 
conn_details = {
    'endpoint': 'https://dbpedia.org/'
}

#name of the datbase to query
db = "sparql"
lang = "en"

def image_to_data(im):
    """
    Image object to bytes object.
    : Parameters
      im - Image object
    : Return
      bytes object.
    """
    with BytesIO() as output:
        im.save(output, format="PNG")
        data = output.getvalue()
    return data

def browse_rel(artist_mbid,limit,offset):
  return musicbrainzngs.browse_releases(artist=artist_mbid,
                                        release_type=["album","single"],release_status=["official"],
                                        includes=["media"], limit=limit, offset=offset)

def convertMillis(millis):
    seconds=int(round((millis/1000)%60))
    minutes=int(round((millis/(1000*60))%60))
    return str(minutes)+":"+str(seconds)

def padding(word:str,length:int):
  print(word)
  paddedWord = word
  paddedWord = paddedWord.strip()
  cnt = len(word)
  padding:int = length-cnt
  for i in range(1,padding):
    paddedWord += " "

  return paddedWord


def getSongsBymbid(release_mbid):
    result = musicbrainzngs.browse_recordings(release=release_mbid,limit=100)
    l =[]
    for r in result["recording-list"]:
        title =""
        length =""
        if "length" in r:
            length = r["length"]
            length = convertMillis(int(length))
        if "title" in r:
            title = r["title"]
        
        l.append((title,length))
    return l

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

#UI
sg.theme('DarkAmber')    # Keep things interesting for your users

layout = [[sg.Text('Search Artist')],      
          [sg.Input(key='-IN-')],      
          [sg.Button('Search'), sg.Exit()],
          [sg.Text('',key='-ARTIST-'),sg.Text('',key='-BIRTHNAME-'),sg.Image(key='-IMAGE-')],
          [sg.Text('',key='-BIRTHDATE-'),sg.Text('',key='-DEATHDATE-')],
          [sg.Text('',key='-AGE-')],
          [sg.Text('',key='-STARTYEAR-'),sg.Text('',key='-ENDYEAR-')],
          [sg.Text('',key='-YEARSACTIVE-')],
          [sg.Multiline(size=(114,15),key='-ABOUT-')],
          [sg.Listbox(values=[], size=(70, 15), key='-RELLIST-', enable_events=True),sg.Listbox(values=[], size=(40, 15), key='-SONGLIST-', enable_events=False)]]      

window = sg.Window('KRSW project', layout)      




def dbPediaArtistQuery(name):
    #connect to the database
    with stardog.Connection(db, **conn_details) as conn:
        #query
        results = conn.select("""
        select distinct *
        where 
        {
            ?artist foaf:name ?name ;
                    owl:sameAs ?musicBrainz ;
                    dbo:activeYearsStartYear ?startYear ;
                    dbo:abstract ?about .

            optional { ?artist dbo:birthName ?birthName . }
            optional { ?artist dbo:birthDate ?birthDate . }
            optional { ?artist dbo:thumbnail ?image .}          
            optional { ?artist dbo:deathDate ?deathDate . }
            optional { ?artist dbo:activeYearsEndYear ?endYear .}
        """
        f"""
        filter langMatches(lang(?about),'{lang}')
        filter regex(?musicBrainz, "musicbrainz") .
        filter regex(?name, "{name}"@{lang}) . """    
        """
        } limit 1
        """
        )
    return results

def calculateAge(born, deathDate):
    if (deathDate == ''):
        today = date.today()
    else:
        today = date.fromisoformat(deathDate)
    if (not isinstance(born, date)):
        born = date.fromisoformat(born)
    try:
        birthday = born.replace(year = today.year)
 
    # born on February 29
    # and the current year is not a leap year
    except ValueError:
        birthday = born.replace(year = today.year,
                 month = born.month + 1, day = 1)
 
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year

def getResultValue(parameter:str):
    if (parameter in result):
        return result[parameter]["value"]
    else:
        return ''

def printNonEmpty(item:str,parameter):
    if (parameter == ''):
        return
    else: 
        print(f'{item}{parameter}')


#GUI main loop
rel_list =[]
releases =[]
song_list =[]
while True:                             
    # The Event Loop
    event, values = window.read() 
    #print(event, values)       
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Search':
        searchName = values['-IN-']
        results = dbPediaArtistQuery(searchName)

        #
        musicbrainzID = ""
        for result in results["results"]["bindings"]:
            musicbrainzID = re.split(r'http://musicbrainz.org/artist/', result["musicBrainz"]["value"])
            about = getResultValue("about")
            name = getResultValue("name")
            birthName = getResultValue("birthName")
            birthDate = getResultValue("birthDate")
            deathDate = getResultValue("deathDate")
            startYear = getResultValue("startYear")
            imgUrl = getResultValue("image")
            imgUrl = imgUrl.split('?')[0]
            print(imgUrl)
            # If deathDate is not empty string, person has died
            hasDied = len(deathDate) > 1
            endYear = (getResultValue("endYear"), False)
            age = ''
            nOYearsActive = ''
            if (endYear == ('', False)):
                endYear = (date.today().year, False)
            else:
                endYear = (int(endYear[0]), True)
            if (startYear != ''):
                nOYearsActive = int(endYear[0]) - int(startYear)
            if (birthDate != ''):
                age = calculateAge(birthDate, deathDate)
            
            window['-ARTIST-'].update("Artist: "+name)
            if(birthName != ""):
                window['-BIRTHNAME-'].update("Birth name: "+birthName)
            else:
                window['-BIRTHNAME-'].update(" ")
            if (birthDate != ""):
                window['-BIRTHDATE-'].update("Birth date: "+birthDate)
            else:
                window['-BIRTHDATE-'].update(" ")
            if(age != ""):
                window['-AGE-'].update("Age: "+ str(age))
            else:
                window['-AGE-'].update(" ")
            if(hasDied):
                window['-DEATHDATE-'].update("Death date: "+deathDate)
            else:
                window['-DEATHDATE-'].update(" ")
            
            window['-STARTYEAR-'].update("Start year: "+startYear)
            if(endYear[1]):
                window['-ENDYEAR-'].update("End year: "+ str(endYear[0]))
            else:
                window['-ENDYEAR-'].update(" ")
            window['-YEARSACTIVE-'].update("Years active: "+ str(nOYearsActive))
            #TODO Fix the image stuff
            #imgUrl = "https://upload.wikimedia.org/wikipedia/commons/d/d9/Test.png"   
            #response = requests.get(imgUrl, stream=True)
            #response.raw.decode_content = True
            #img = ImageQt.Image.open(response.raw)
            #data = image_to_data(img)

            #window['-IMAGE-'].update(data=response.raw.read())
            
          
                
            window['-ABOUT-'].update(about)
            

        #
        releases = getReleasesByMbID(musicbrainzID[1])
        rel_list = []
        for r in releases:
            title = str(r[1])
            #title = padding(title,70)
            relDate = str(r[3])
            tracks = str(r[2])
          
            rel_list.append("{0} : {1} Tracks:{2}".format(title,relDate,tracks))

        window["-RELLIST-"].update(rel_list)

    if event == '-RELLIST-' :
        index = window['-RELLIST-'].GetIndexes()[0] #becuase of multiple selections
        mbid = releases[index][0] 
        songs = getSongsBymbid(mbid)
        song_list =[]
        for s in songs:
            st = str(s[0]) + "  " + str(s[1])
            song_list.append(st)
            window['-SONGLIST-'].update(song_list)

window.close()