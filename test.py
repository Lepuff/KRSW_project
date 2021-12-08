
import json
import musicbrainzngs
import sys
#General stuff
musicbrainzngs.set_useragent("KSRW_project","1.0",contact=None)
musicbrainzngs.set_hostname("musicbrainz.org",use_https=False)
def convertMillis(millis):
    seconds=int(round((millis/1000)%60))
    minutes=int(round((millis/(1000*60))%60))
    return str(minutes)+":"+str(seconds)


def getSongsBymbid(release_mbid):
    result = musicbrainzngs.browse_recordings(release=release_mbid,limit=100)
    l =[]
    for r in result["recording-list"]:
        title = r["title"]
        length = r["length"]
        length = convertMillis(int(length))
        l.append((title,length))
    return l

def getReleasesByMbID(artist_mbid):
    #label = "71247f6b-fd24-4a56-89a2-23512f006f0c"
    #label ="b95ce3ff-3d05-4e87-9e01-c97b66af13d4"
    limit = 100
    offset = 0
    releases = []
    page = 1
    #print("fetching page number %d.." % page)
    result = musicbrainzngs.browse_releases(artist=artist_mbid,
                        release_type=["album","single"],release_status=["official"],includes=["media"], limit=limit, offset=offset)
    page_releases = result['release-list']
    releases += page_releases
    # release-count is only available starting with musicbrainzngs 0.5
    if "release-count" in result:
            count = result['release-count']
            print("")

    while len(page_releases) >= limit:
        offset += limit
        page += 1
        print("fetching page number %d.." % page)
        result = musicbrainzngs.browse_releases(artist=artist_mbid,
                            release_type=["album","single"],release_status=["official"],includes=["media"], limit=limit, offset=offset)
        page_releases = result['release-list']
        releases += page_releases
    print("")

    releases_list =[]
    u_list = []
    for r in releases:
        trackcount = r["medium-list"][0]["track-count"] 
        #print("id : "+r["id"]+"   title: "+r["title"] + " track count : "+str(trackcount))
        if r["title"] not in u_list:
            u_list.append(r["title"])
            releases_list.append((r["id"],r["title"],r["date"],trackcount))
    return releases_list

#releases_list = getReleasesByMbID("b95ce3ff-3d05-4e87-9e01-c97b66af13d4")

releases_list = getSongsBymbid("fd82c0c8-687c-32f6-b31e-0b2c585e006b")


for rel in releases_list:
    print(rel)

