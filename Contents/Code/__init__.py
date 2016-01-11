NAME = "subsonicPlex"
ART = 'art-default.png'
ICON = 'icon-default.png'
ICON_SEARCH = 'icon-search.png'
CACHE_INTERVAL = 1



ARTIST = "{http://subsonic.org/restapi}artist"
ALBUM = "{http://subsonic.org/restapi}album"
ALBUMLIST = "{http://subsonic.org/restapi}albumList"
SONG = "{http://subsonic.org/restapi}song"
ENTRY = "{http://subsonic.org/restapi}entry"
CHILD = "{http://subsonic.org/restapi}child"
DIRECTORY = "{http://subsonic.org/restapi}directory"
SHORTCUT = "{http://subsonic.org/restapi}shortcut"
PLAYLIST = "{http://subsonic.org/restapi}playlist"

SUBSONIC_API_VERSION = "1.9.0"
SUBSONIC_CLIENT = "plex"


import binascii
####################################################################################################

# This function is initially called by the PMS framework to initialize the plugin. This includes
# setting up the Plugin static instance along with the displayed artwork.
def Start():

    HTTP.CacheTime = 600

    # Initialize the plugin
    Plugin.AddViewGroup("List", viewMode = "List", mediaType = "items")
    Plugin.AddViewGroup("InfoList", viewMode = "InfoList", mediaType = "items")
    Plugin.AddViewGroup("Album", viewMode = "Songs", mediaType = "items")
    # Setup the artwork associated with the plugin
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    ObjectContainer.view_group = "Album"

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    TrackObject.thumb = R(ICON)

####################################################################################################

@handler('/music/subsonicPlex', NAME, thumb = ICON, art = ART)
def MainMenu():

    oc = ObjectContainer(title1 = NAME)
    #oc.add(InputDirectoryObject(key = Callback(Search), title = "Tracks Search...", prompt = "Search for Tracks", thumb = R(ICON_SEARCH)))
    #oc.add(InputDirectoryObject(key = Callback(UsersSearch), title = "Users Search...", prompt = "Search for Users", thumb = R(ICON_SEARCH)))
    #oc.add(InputDirectoryObject(key = Callback(GroupsSearch), title = "Groups Search...", prompt = "Search for Groups", thumb = R(ICON_SEARCH)))
    oc.add(DirectoryObject(title=L("List by Artists"), key = Callback(getArtists)))
    oc.add(DirectoryObject(title=L("List by Index"), key = Callback(getIndexes)))
    oc.add(DirectoryObject(title=L("Newest"), key = Callback(getAlbumList, ypeL="newest")))
    oc.add(DirectoryObject(title=L("Playlist"), key = Callback(getPlaylists)))
    oc.add(DirectoryObject(title=L("Random Songs"), key = Callback(getRandomSongs)))
    oc.add(DirectoryObject(title=L("Test"), key = Callback(getRandomSongs)))
    oc.add(PrefsObject(title="Preferences"))
    return oc

####################################################################################################
#create a menu listing all artists
@route('/music/subsonicPlex/getArtists')
def getArtists():
  if not serverStatus():
   return ObjectContainer(header="Can't Connect", message="Check that your username, password and server address are entered correctly.")
  oc = ObjectContainer(title2="Artists")
  element = XML.ElementFromURL(makeURL("getArtists.view"), cacheTime=CACHE_INTERVAL)
  #add all artists
  for item in searchElementTree(element, ARTIST):
    title = item.get("name")
    id = item.get("id")
    key = '/music/subsonicPlex/getArtist/' + id
    rating_key  = id
    oc.add(DirectoryObject(title=title, key=key))

  return oc

#create a menu with all albums for selected artist
@route('/music/subsonicPlex/getArtist/{artistID}')
def getArtist(artistID):
  element = XML.ElementFromURL(makeURL("getArtist.view", id=artistID), cacheTime=CACHE_INTERVAL)
  artistName = element.find(ARTIST).get("name")
  oc = ObjectContainer(title2=artistName)
  for item in searchElementTree(element, ALBUM):
    duration = item.get("duration")
    if duration:
      duration = 1000 * int(duration)
    else:
      duration = 0
    title = item.get("name")
    id = item.get("id")
    #key = Callback(getAlbum, albumID=id)
    key = '/music/subsonicPlex/getAlbum/' + id
    rating_key = id
    element1 = XML.ElementFromURL(makeURL("getAlbum.view", id=id), cacheTime=CACHE_INTERVAL)
    for item1 in searchElementTree(element1, SONG):
      parent = item1.get("parent")
    #parent = Callback(getart, albumID=id)
    url1        = makeURL("getCoverArt.view", id=parent)
    thumb = Callback(Thumb, url=url1)
    #oc.add(DirectoryObject(key=key, title=title, duration=duration, thumb=thumb))
    oc.add(DirectoryObject(key=key,title=title, duration=duration, thumb=thumb))
  return oc 

#create a menu with all songs for selected album
@route('/music/subsonicPlex/getSong/{SongID}')
def getSong(SongID):
  #set audio format based on prefs
  container = Prefs['format']
  if container == 'mp3':
    audio_codec = AudioCodec.MP3
  elif container == 'aac':
    audio_codec = AudioCodec.AAC

  element = XML.ElementFromURL(makeURL("getSong.view", id=SongID), cacheTime=CACHE_INTERVAL)
  title       = element.find(SONG).get("title")
  parent      = element.find(SONG).get("parent")
  rating_key  = SongID
  duration    = element.find(SONG).get("duration")
  if duration:
    duration = 1000 * int(duration)
  else:
    duration = 0
  artist      = element.find(SONG).get("artist")
  album       = element.find(SONG).get("album")
  url1        = makeURL("getCoverArt.view", id=parent)
  url = makeURL("stream.view", id=SongID, format=container)
  oc = ObjectContainer(title1=title)
  oc.add(TrackObject(
  title = title,
  album = album,
  artist = artist,
  thumb = Callback(Thumb, url=url1),
  duration = duration,
  key = '/music/subsonicPlex/getSong/' + SongID, #might need to change this line eventually to return metadata instead of playing track url
  rating_key=rating_key,
  items = [
  MediaObject(
  container = 'mp3',
  audio_codec = audio_codec,
  audio_channels = 2,
  parts = [
  PartObject(key = url)
  ]
  )
  ]))
  return oc

#create a menu with all songs for selected album
@route('/music/subsonicPlex/getart/{albumID}')
def getart(albumID):
 element = XML.ElementFromURL(makeURL("getAlbum.view", id=albumID), cacheTime=CACHE_INTERVAL)
 for item in searchElementTree(element, SONG):
   parent      = item.get("parent")
   url1        = makeURL("getCoverArt.view", id=parent)
   thumb = Callback(Thumb, url=url1)
 return thumb

#create a menu with all newest album
@route('/music/subsonicPlex/getAlbumList/{ypeL}')
def getAlbumList(ypeL):
  element = XML.ElementFromURL(makeURL("getAlbumList.view", type=ypeL), cacheTime=CACHE_INTERVAL)
  oc = ObjectContainer(title2="Newest", view_group = "Album")
  oc.view_group = "Album" 
  for item in searchElementTree(element, ALBUM):
    cover = item.get("coverArt")
    title = item.get("album")
    artist = item.get("artist")
    id = item.get("id")
    parent = item.get("parent")
    key = '/music/subsonicPlex/getMusicDirectory/' + id
    url1 = makeURL("getCoverArt.view", id=id)
    thumb = Callback(Thumb, url=url1)
    oc.add(DirectoryObject(title=artist+" - "+title, key = '/music/subsonicPlex/getMusicDirectory/' + id, thumb=thumb))
  return oc 

#create a menu with all songs for selected album
@route('/music/subsonicPlex/getAlbum/{albumID}')
def getAlbum(albumID):
  #set audio format based on prefs
  container = Prefs['format']
  if container == 'mp3':
    audio_codec = AudioCodec.MP3
  elif container == 'aac':
    audio_codec = AudioCodec.AAC
  
  #populate the track listing
  element = XML.ElementFromURL(makeURL("getAlbum.view", id=albumID), cacheTime=CACHE_INTERVAL)
  albumName = element.find(ALBUM).get("name")
  oc = ObjectContainer(title1=albumName, view_group = "Album")
  oc.view_group = "Album"
  for item in searchElementTree(element, SONG):
    title       = item.get("title")
    artist      = item.get("artist")
    album       = item.get("album")
    id          = item.get("id")
    parent      = item.get("parent")
    url1        = makeURL("getCoverArt.view", id=parent)
    rating_key  = id
    duration = item.get("duration")
    if duration:
      duration = 1000 * int(duration)
    else:
      duration = 0
    url = makeURL("stream.view", id=id, format=container)
    url2 = makeURL("download.view", id=id, format=container)
    oc.add(TrackObject(
      title = title,
      album = album,
      artist = artist,
      thumb = Callback(Thumb, url=url1),
      duration = duration,
      key = '/music/subsonicPlex/getSong/' + id, #might need to change this line eventually to return metadata instead of playing track url
      rating_key=rating_key,
      items = [
        MediaObject(
          container = 'mp3',
          audio_codec = audio_codec,
          audio_channels = 2,
          parts = [
            PartObject(key = url, duration=duration)
          ]
       )
      ]))
  return oc

#create a menu with all songs for selected album
@route('/music/subsonicPlex/getAlbum1/{albumID}')
def getAlbum1(albumID):
  #set audio format based on prefs
  container = Prefs['format']
  if container == 'mp3':
    audio_codec = AudioCodec.MP3
  elif container == 'aac':
    audio_codec = AudioCodec.AAC
  
  #populate the track listing
  element = XML.ElementFromURL(makeURL("getAlbum.view", id=albumID), cacheTime=CACHE_INTERVAL)
  albumName = element.find(ALBUM).get("name")
  oc = ObjectContainer(title1=albumName)
  for item in searchElementTree(element, SONG):
    title       = item.get("title")
    artist      = item.get("artist")
    album       = item.get("album")
    id          = item.get("id")
    parent      = item.get("parent")
    url1        = makeURL("getCoverArt.view", id=parent)
    rating_key  = id
    duration = item.get("duration")
    if duration:
      duration = 1000 * int(duration)
    else:
      duration = 0
    url = makeURL("stream.view", id=id, format=container)
    url2 = makeURL("download.view", id=id, format=container)
    oc.add(TrackObject(
      title = title,
      album = album,
      artist = artist,
      thumb = Callback(Thumb, url=url1),
      duration = duration,
      key = '/music/subsonicPlex/getSong/' + id, #might need to change this line eventually to return metadata instead of playing track url
      rating_key=rating_key,
      items = [
        MediaObject(
          container = 'mp3',
          audio_codec = audio_codec,
          audio_channels = 2,
          parts = [

            PartObject(key = url, duration=duration)
          ]
       )
      ]))
  return oc


#create a menu listing all indexes
@route('/music/subsonicPlex/getIndexes')
def getIndexes():
  if not serverStatus():
   return ObjectContainer(header="Can't Connect", message="Check that your username, password and server address are entered correctly.")
  oc = ObjectContainer(title1="Index")
  element = XML.ElementFromURL(makeURL("getIndexes.view"), cacheTime=CACHE_INTERVAL)
  #add all artists
 
  for item in searchElementTree(element, SHORTCUT):
    title       = item.get("name")
    id          = item.get("id")
    key        = '/music/subsonicPlex/getMusicDirectory/' + id
    rating_key  = id
    oc.add(DirectoryObject(title=title, key=key)) 
 
  for item in searchElementTree(element, ARTIST):
    title       = item.get("name")
    id          = item.get("id")
    key        = '/music/subsonicPlex/getMusicDirectory/' + id
    rating_key  = id
    oc.add(DirectoryObject(title=title, key=key))

  return oc

#create a menu listing all playlists
@route('/music/subsonicPlex/getPlaylists')
def getPlaylists():
  if not serverStatus():
   return ObjectContainer(header="Can't Connect", message="Check that your username, password and server address are entered correctly.")
  oc = ObjectContainer(title1="Playlists")
  element = XML.ElementFromURL(makeURL("getPlaylists.view"), cacheTime=CACHE_INTERVAL)
  #add all artists
 
  for item in searchElementTree(element, PLAYLIST):
    title       = item.get("name")
    id          = item.get("id")
    comment     = item.get("comment")
    key        = '/music/subsonicPlex/getPlaylist/' + id
    rating_key  = id
    oc.add(DirectoryObject(title=title, key=key))
  return oc

#create a menu with all songs for selected album
@route('/music/subsonicPlex/getPlaylist/{playlistID}')
def getPlaylist(playlistID):
  #set audio format based on prefs
  container = Prefs['format']
  if container == 'mp3':
    audio_codec = AudioCodec.MP3
  elif container == 'aac':
    audio_codec = AudioCodec.AAC
  
  #populate the track listing
  element = XML.ElementFromURL(makeURL("getPlaylist.view", id=playlistID), cacheTime=CACHE_INTERVAL)
  albumName = element.find(PLAYLIST).get("name")
  oc = ObjectContainer(title1=albumName)
  for item in searchElementTree(element, ENTRY):
    title       = item.get("title")
    artist      = item.get("artist")
    album       = item.get("album")
    id          = item.get("id")
    parent      = item.get("parent")
    url1        = makeURL("getCoverArt.view", id=parent)
    rating_key  = id
    duration = item.get("duration")
    if duration:
      duration = 1000 * int(duration)
    else:
      duration = 0
    url = makeURL("stream.view", id=id, format=container)
    url2 = makeURL("download.view", id=id, format=container)
    oc.add(TrackObject(
      title = title,
      album = album,
      artist = artist,
      thumb = Callback(Thumb, url=url1),
      duration = duration,
      key = '/music/subsonicPlex/getSong/' + id, #might need to change this line eventually to return metadata instead of playing track url
      rating_key=rating_key,
      items = [
        MediaObject(
          container = 'mp3',
          audio_codec = audio_codec,

          audio_channels = 2,
          parts = [

            PartObject(key = url, duration=duration)
          ]
       )
      ]))
  return oc

#create a menu with all songs for selected album
@route('/music/subsonicPlex/getRandomSongs')
def getRandomSongs():
  #set audio format based on prefs
  container = Prefs['format']
  if container == 'mp3':
    audio_codec = AudioCodec.MP3
  elif container == 'aac':
    audio_codec = AudioCodec.AAC
  
  #populate the track listing
  element = XML.ElementFromURL(makeURL("getRandomSongs.view", size=Prefs['random']), cacheTime=CACHE_INTERVAL)

  oc = ObjectContainer(title1='Random '+ Prefs['random'] + ' chansons')
  for item in searchElementTree(element, SONG):
    title       = item.get("title")
    album       = item.get("album")
    artist       = item.get("artist")
    #if artist:
    # title = title  + " [" + artist + "]"
    id          = item.get("id")
    parent      = item.get("parent")
    url1        = makeURL("getCoverArt.view", id=parent)
    rating_key  = id
    duration = item.get("duration")
    if duration:
      duration = 1000 * int(duration)
    else:
      duration = 0
    url = makeURL("stream.view", id=id, format=container)
    url2 = makeURL("download.view", id=id, format=container)
    oc.add(TrackObject(
      title = title,
      album = album,
      artist = artist,
      thumb = Callback(Thumb, url=url1),
      duration = duration,
      key = '/music/subsonicPlex/getSong/' + id, #might need to change this line eventually to return metadata instead of playing track url
      rating_key=rating_key,
      items = [
        MediaObject(
          container = 'mp3',
          audio_codec = audio_codec,
          audio_channels = 2,
          parts = [
            PartObject(key = url, duration=duration)
          ]
       )
      ]))
  return oc
  
#create a menu with all albums for selected artist
@route('/music/subsonicPlex/getMusicDirectory/{artistID}')
def getMusicDirectory(artistID):
  #set audio format based on prefs
  container = Prefs['format']
  if container == 'mp3':
    audio_codec = AudioCodec.MP3
  elif container == 'aac':
    audio_codec = AudioCodec.AAC
	
  element = XML.ElementFromURL(makeURL("getMusicDirectory.view", id=artistID), cacheTime=CACHE_INTERVAL)
  artistName = element.find(DIRECTORY).get("name")
  oc = ObjectContainer(title1=artistName)
  for item in searchElementTree(element, CHILD):
    id          = item.get("id")
    title       = item.get("album")
    if not title:
        title      = item.get("artist")
    rating_key  = id
    isDir       = item.get("isDir")
    url1        = makeURL("getCoverArt.view", id=id)
    url         = makeURL("stream.view", id=id, format=container)
    if isDir == 'true':
      oc.add(DirectoryObject(title=title, key= '/music/subsonicPlex/getMusicDirectory/' + id, thumb = Callback(Thumb, url=url1)))
    elif isDir == 'false': 
      duration = item.get("duration")
      if duration:
       duration = 1000 * int(duration)
      else:
       duration = 0
      title       = item.get("title")
      artist      = item.get("artist")
      album       = item.get("album")
      oc.title1   = album	
      oc.add(TrackObject(title = title, thumb = Callback(Thumb, url=url1),artist=title,album=album,duration = duration,key = '/music/subsonicPlex/getSong/' + id,
      rating_key=rating_key,
      items = [
      MediaObject(
      container = 'mp3',
      audio_codec = audio_codec,
      audio_channels = 2,
      parts = [
      PartObject(key = url, duration=duration)
      ]
      )
      ]))
  return oc

#
@route('/music/subsonicPlex/Thumb')
def Thumb(url):
  try:
    data       = HTTP.Request(url, cacheTime=CACHE_INTERVAL).content
    return DataObject(data, 'image/jpeg')
  except:
    return Redirect(R(ICON))
	
#construct a http GET request from a view name and parameters
def makeURL(view, **parameters):
  url = Prefs['server']
  url += "rest/" + view + "?"
  parameters['u'] = Prefs['username']
  parameters['p'] = "enc:" + binascii.hexlify(Prefs['password'])
  parameters['v'] = SUBSONIC_API_VERSION
  parameters['c'] = SUBSONIC_CLIENT
  for param in parameters:
    url += param + "=" + parameters[param] + "&"
  return url

#recursively search etree and return list with all the elements that match  
def searchElementTree(element, search):
  matches = element.findall(search)
  if len(element):
    for e in list(element):
      matches += searchElementTree(e, search)
  return matches
	
#check that media server is accessible
def serverStatus():
  #check that Preferences have been set
  if not (Prefs['username'] and Prefs['password'] and Prefs['server'] and Prefs['random']):
    return False
  #try to ping server with credentials
  elif XML.ElementFromURL(makeURL("ping.view"), cacheTime=CACHE_INTERVAL).get("status") != "ok":
    return False
  #connection is successful, return True and proceed!
  else:
    return True

#check int
def is_int(x):
  try:
    int(x)
    return True
  except ValueError:
    return False

#Plex calls this functions anytime Prefs are changed
def ValidatePrefs():
  if Prefs['server'][-1] != '/':
    return ObjectContainer(header="Check Server Address", message="Server address must end with a slash character ie http://127.0.0.1:8080/")
  elif is_int(Prefs['random']) == False:
    return ObjectContainer(header="Check Random number", message="Random number must be an INTEGER")
  elif not serverStatus():
    return ObjectContainer(header="Can't Connect", message="Check that your username, password and server address are entered correctly.")
