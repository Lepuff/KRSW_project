#imports
import PySimpleGUI as sg
import stardog
import musicbrainzngs
import re
from datetime import date
import string


#set endpoints
musicbrainzngs.set_useragent("KSRW_project","1.0",contact=None)
musicbrainzngs.set_hostname("musicbrainz.org",use_https=False)

#connect to the DBpedia endpoint 
conn_details = {
    'endpoint': 'https://dbpedia.org/'
}

#name of the datbase to query
db = "sparql"
lang = "en"


def millisToStr(millis):
    seconds=int(round((millis/1000)%60))
    minutes=int(round((millis/(1000*60))%60))
    return str(minutes)+":"+str(seconds)

# get all the tracks connected to a musicbrainz release id
def getSongsBymbid(release_mbid):
    result = musicbrainzngs.browse_recordings(release=release_mbid,limit=100)
    l =[]
    for r in result["recording-list"]:
        title =""
        length =""
        if "length" in r:
            length = r["length"]
            length = millisToStr(int(length))
        if "title" in r:
            title = r["title"]
        
        l.append((title,length))
    return l


# get releases connected to to a artist, subfunction becuase of the limit on requests on the musicbrainz server, see next function.
def browse_rel(artist_mbid,limit,offset):
  return musicbrainzngs.browse_releases(artist=artist_mbid,
                                        release_type=["album","single"],release_status=["official"],
                                        includes=["media"], limit=limit, offset=offset)

#get all the releases connected to an musicbrainz artist id
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

#UI
sg.theme('Black')

layout = [[sg.Text('Search Artist')],      
          [sg.Input(key='-IN-')],      
          [sg.Button('Search'), sg.Exit()],
          [sg.Text('',key='-ARTIST-'),sg.Text('',key='-BIRTHNAME-'),sg.Image(size=(50,50),key='-IMAGE-')],
          [sg.Text('',key='-BIRTHDATE-'),sg.Text('',key='-DEATHDATE-')],
          [sg.Text('',key='-AGE-')],
          [sg.Text('',key='-STARTYEAR-'),sg.Text('',key='-ENDYEAR-')],
          [sg.Text('',key='-YEARSACTIVE-')],
          [sg.Multiline(size=(114,15),key='-ABOUT-')],
          [sg.Listbox(values=[], size=(70, 15), key='-RELLIST-', enable_events=True),sg.Listbox(values=[], size=(40, 15), key='-SONGLIST-', enable_events=False)]]      

window = sg.Window('KRSW project', layout)      

def cap_search(s):
  return re.sub("(^|\s)(\S)", lambda m: m.group(1) + m.group(2).upper(), s)

def resetGuiWindow():
    window['-BIRTHNAME-'].update('')
    window['-ARTIST-'].update('')
    window['-BIRTHDATE-'].update('')
    window['-DEATHDATE-'].update('')
    window['-AGE-'].update('')
    window['-STARTYEAR-'].update('')
    window['-YEARSACTIVE-'].update('')
    window['-ABOUT-'].update('')
    window['-RELLIST-'].update('')
    window['-IMAGE-'].update('')
    window['-SONGLIST-'].update('')

#GUI main loop
rel_list =[]
releases =[]
song_list =[]
size = (50, 50)
while True:                             
    # The Event Loop
    event, values = window.read() 
    #print(event, values) #for debugging dont remove      
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Search':
        searchName = str(values['-IN-'])
        results = dbPediaArtistQuery(cap_search(searchName))
        musicbrainzID = ""
        for result in results["results"]["bindings"]:
            musicbrainzID = re.split(r'http://musicbrainz.org/artist/', result["musicBrainz"]["value"])
            about = getResultValue("about")
            name = getResultValue("name")
            birthName = getResultValue("birthName")
            birthDate = getResultValue("birthDate")
            deathDate = getResultValue("deathDate")
            startYear = getResultValue("startYear")
            

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
            
         
            window['-ABOUT-'].update(about)

        try:
            print(musicbrainzID[1])
        except IndexError:
            resetGuiWindow()
            window['-ARTIST-'].update('No Artist Found')

        else:
            releases = getReleasesByMbID(musicbrainzID[1])
            rel_list = []
            for r in releases:
                title = str(r[1])
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