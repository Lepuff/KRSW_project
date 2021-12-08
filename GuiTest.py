from queue import Empty
import PySimpleGUI as sg      
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


#sg.theme('DarkAmber')    # Keep things interesting for your users

layout = [[sg.Text('Search Artist')],      
          [sg.Input(key='-IN-')],      
          [sg.Button('Search'), sg.Exit()],
          [sg.Text('Artist: '),sg.Text('',key='-ARTIST-')],
          [sg.Text('Age: '),sg.Text('',key='-AGE-')],
          [sg.Text('Start year: '),sg.Text('',key='-STARTYEAR-')],
          [sg.Text('Years active: '),sg.Text('',key='-YEARSACTIVE-')],
          [sg.Multiline(size=(114,15),key='-TEXTFEILD-')],
          [sg.Listbox(values=[], size=(70, 20), key='-RELLIST-', enable_events=True),sg.Listbox(values=[], size=(40, 20), key='-SONGLIST-', enable_events=False)]]      

window = sg.Window('KRSW project', layout)      





rel_list =[]
releases =[]
song_list =[]
while True:                             # The Event Loop
    event, values = window.read() 
    print(event, values)       
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Search':
        searchName = values['-IN-']
        releases = getReleasesByMbID(searchName)

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