#!/usr/bin/env python
"""
Simple wrapper-lib for accessing the http://www.simpy.com/ REST API via python.
See http://simpytools.sourceforge.net for details, and libs in other languages

Copyright:
    Copyright (c) 2005-2007, Benjamin Reitzammer <benjamin@nur-eine-i.de>, All rights reserved.
    
License:
    This program is free software. You can distribute/modify this program under 
    the terms of either 
    
    * GNU LGPL, Lesser General Public License version 2.1 available at http://www.gnu.org/licenses/lgpl.txt
    or 
    * Apache License Version 2.0 available at http://www.apache.org/licenses/LICENSE-2.0.txt 
    
Synopsis:
    # get and store links in files matching a query
    client = SimpyClient('user', 'passwd')
    links = client.getLinks( {'limit':20, 'q':'+tags:"programming" +tags:"trails"'} )
    for i, link in enumerate(links):
        s = urllib2.urlopen(link.url)
        if s is not None: file(str(i)+".html", 'w+').write(s.read())
        else: print "URL "+link.url+" was not handled"
        
Supported Calls:
      * GetTags, RemoveTag, RenameTag, MergeTags, SplitTag
      * GetLinks, SaveLink, DeleteLink 
      * GetWatchlists, GetWatchlist 
      * GetNotes, SaveNote
        
Required: 
    Python 2.3 or later (may run with older version, but this is untested)

Acknowledgements:
    This lib was heavily influenced by http://delicious-py.berlios.de/
    
"""

#
# FIXME handle status response in non-void calls, if errors occur
#

__author__ = "Benjamin Reitzammer <benjamin@nur-eine-i.de>"
__version__ = "1.1"


import urllib2, urllib, re, datetime, os
import xml.parsers.expat

### 
### set these to your own values if you know what you are doing 
###


# specifies the base URL, no leading slash please
if os.environ.has_key('SIMPY_BASE_URL'):
    BASE_URL = os.environ['SIMPY_BASE_URL']
else: 
    BASE_URL = "http://www.simpy.com/simpy/api/rest"


# 'Host:' Header used during basic HTTP auth
HOST = "www.simpy.com"


# Realm used as WWW-Authenticate Header during HTTP auth
REALM = "/simpy/api/rest" 


# specified the 'User-Agent' Header 
USER_AGENT = "Mozilla (compatible; simpyapi-python "+ __version__ +")"


# the URLs of the specific API calls 
GETLINKS_URL   = "/GetLinks.do"
SAVELINK_URL   = "/SaveLink.do"
DELETELINK_URL = "/DeleteLink.do"

GETTAGS_URL   = "/GetTags.do"
REMOVETAG_URL = "/RemoveTag.do"
RENAMETAG_URL = "/RenameTag.do"
MERGETAGS_URL = "/MergeTags.do"
SPLITTAG_URL  = "/SplitTag.do"

GETNOTES_URL   = "/GetNotes.do"
SAVENOTE_URL   = "/SaveNote.do"
DELETENOTE_URL = "/DeleteNote.do"

GETWATCHLISTS_URL = "/GetWatchlists.do"
GETWATCHLIST_URL  = "/GetWatchlist.do"

        

class SimpyClient:
    """The client abstraction of simpy's REST API.
    
    Use instances of this class to communicate with the REST API. 
    
    All calls that modify data on the server side are issued as POST request,
    while reading requests are performed as GET requests.
    """
    
    def __init__(self, user, passwd):
        """Create an instance of this class
        
        Parameters:
          user   - the username to use when authenticating against the API
          passwd - the password to use when authenticating against the API
        """
        self.user, self.passwd = user, passwd
        
        
    def getTags(self, limit=0):
        """Makes a call to GetTags() of the simpy API
        
        Parameters
            limit - the number of tags returned by the call, default is 0, which gets all tags
            
        Return:
          A list of dictionaries that contain the values for 'count' and 'tag' 
          as returned by the call to the API, never <None>
        """
        return parseTags( GET(url(GETTAGS_URL), self.user, self.passwd, {'limit': str(limit)}) )
        
    def removeTag(self, tag=None):
        """Makes a call to RemoveTag() of the simpy API, removing the specified tag
        
        Parameters
            tag - the tag to delete
        
        Return:
          A dictionary containing 'code' and 'message' of the response. A code
          unequal zero indicates an error, or None if the provided tag string is 
          None
        """
        if tag is None: 
            return None
        else:
            return parseVoidResponse( POST(url(REMOVETAG_URL), self.user, self.passwd, {'tag': tag}) )
        
    def renameTag(self, fromTag=None, toTag=None):
        """Makes a call to RenameTag() of the simpy API, renaming the fromTag to 
        the value specified by toTag
        
        Parameters
            fromTag - the tag which should be renamed
            toTag - the target name the 'fromTag' should be renamed to
        
        Return:
          A dictionary containing 'code' and 'message' of the response. A code
          unequal zero indicates an error, or None if any of the provided tag 
          strings is None
        """
        if fromTag is None or toTag is None: 
            return None
        else:
            return parseVoidResponse( POST(url(RENAMETAG_URL), \
                                           self.user, \
                                           self.passwd, \
                                           {'fromTag': fromTag, 'toTag': toTag}) )
        
    def mergeTags(self, fromTag1=None, fromTag2=None, toTag=None):
        """Makes a call to MergeTags() of the simpy API, merging the fromTag1 
        and fromTag2 to the tag specified by toTag
        
        Parameters
            fromTag1 - the first tag that should be merged
            fromTag2 - the second tag that should be merged
            toTag - the target tag that the two tags should be merged to
        
        Return:
          A dictionary containing 'code' and 'message' of the response. A code
          unequal zero indicates an error, or None if any of the provided tag 
          strings is None
        """
        if fromTag1 is None or fromTag2 is None or toTag is None: 
            return None
        else:
            return parseVoidResponse( POST(url(MERGETAGS_URL), \
                                           self.user, \
                                           self.passwd, \
                                           {'fromTag1': fromTag1, 'fromTag2': fromTag2, 'toTag': toTag}) )
        
    def splitTag(self, tag=None, toTag1=None, toTag2=None):
        """Makes a call to SplitTag() of the simpy API, splitting the tag specified 
        by 'tag' to the tags specified by toTag1 and toTag2
        
        Parameters
            tag - the tag that should be split in two new tags
            toTag1 - the first tag the source tag should be merged to
            toTag2 - the second tag the source tag should be merged to
        
        Return:
          A dictionary containing 'code' and 'message' of the response. A code
          unequal zero indicates an error, or None if any of the provided tag 
          strings is None
        """
        if tag is None or toTag1 is None or toTag2 is None: 
            return None
        else:
            return parseVoidResponse( POST(url(SPLITTAG_URL), \
                                           self.user, \
                                           self.passwd, \
                                           {'tag': tag, 'toTag1': toTag1, 'toTag2': toTag2}) )
        
    def getLinks(self, params={}):
        """Makes a call to GetLinks() of the simpy API  
        
        Parameters:
            params - optional dictionary of parameters, that will be sent with the call.
                Valid parameters are:
                <q> A query string that forces the API call to return only the 
                   matching links. You can use the usual Simpy search syntax and 
                   search fields.
                <limit> Limits the number of links returned.
                <date> This parameter should not be used in combination with 
                    the afterDate and beforeDate parameters. It limits the links 
                    returned to links added on the given date.
                <afterDate> This parameter should be used in combination with the
                    beforeDate parameter. It limits the links returned to links
                    added after the given date, excluding the date specified.
                <beforeDate> This parameter should be used in combination with 
                    the afterDate parameter. It limits the links returned to 
                    links added before the given date, excluding the date specified.
            
        Return:
            A list of Link-objects, that's never <None>
        """
        if params is None: params = {}
        return parseData( GET(url(GETLINKS_URL), self.user, self.passwd, params) )

    def saveLink(self, link):
        """Makes a call to SaveLink() of the simpy API
        
        Parameters:
            link - a Link object representing the link to be saved
        
        Return:
          A dictionary containing 'code' and 'message' of the response. A code
          unequal zero indicates an error.
        """
        if link._validate(): 
            return parseVoidResponse( POST(url(SAVELINK_URL), self.user, self.passwd, link.toPost()) )
        else: 
            raise ValidationError(link)     
        
    def deleteLink(self, href):
        """Makes a call to DeleteLink() of the simpy API, deleting the bookmark
        specified by the parameter 'href'
        
        Parameters:
            href - the 'http' URL that represents the bookmark that should be saved
        
        Return:
          A dictionary containing 'code' and 'message' of the response. A code
          unequal zero indicates an error.
        """
        #### FIXME add a check if the URL starts with http://
        if href is None : 
            raise ValidationError(href)     
        else: 
            return parseVoidResponse( POST(url(DELETELINK_URL), self.user, self.passwd, {'href': href}) )
        
    def getNotes(self, query='', limit=0):
        """Makes a call to GetNotes() of the simpy API
        
        Parameters:
          query - the query string, that denotes the search query the notes are searched for
          limit - the number of items returned by the request, default is 0, which retrieves all notes
                   
        Return: 
            A list of Note-objects, or <None> if the 'query' provided is <None>
        """
        if query is None: query = ''
        return parseData( GET(url(GETNOTES_URL), self.user, self.passwd, {'q': query, 'limit': str(limit)}) )
        
    def saveNote(self, note):
        """Makes a call to SaveNote() of the simpy API
        
        Return:
          A dictionary containing 'code' and 'message' of the response. A code
          unequal zero indicates an error.
        """
        if note._validate():
            return parseVoidResponse( POST(url(SAVENOTE_URL), self.user, self.passwd, note.toPost()) )
        else: 
            raise ValidationError(note)

    def deleteNote(self, note):
        """Makes a call to DeleteNote() of the simpy API
        
        Return:
          A dictionary containing 'code' and 'message' of the response. A code
          unequal zero indicates an error.
        """
        if note is None or note.ident is None:
            raise ValidationError(note)
        else:
            return parseVoidResponse( POST(url(DELETENOTE_URL), self.user, self.passwd, { 'noteId': note.ident }) )


    def getWatchlists(self):
        """Makes a call to GetWatchlists() of the simpy API
        
        Return:
        """
        return parseWatchlists( GET(url(GETWATCHLISTS_URL), self.user, self.passwd) )
        
    def getWatchlist(self, watchlistId):
        """Makes a call to GetWatchlist() of the simpy API
        
        Return:
            A Watchlist object if the provided Id was a valid watchlist id, None
            otherwise
        """
        arr = parseWatchlists( GET(url(GETWATCHLIST_URL), self.user, self.passwd, {'watchlistId': watchlistId}) )
        if len(arr) > 0: return arr[0]
        else: None
        
        

class ValidationError:
    """Signals that it was tried to save an incomplete/invalid object.
    """
    obj = None
    def __init__(self, obj):
        self.obj = obj
        
    def __str__(self):
        return "Failed to validate object:", self.obj

        
        
class PostRedirectHandler(urllib2.HTTPRedirectHandler):
    """This is needed when making a POST request to simpy.
    
    It's needed, e.g. when saving notes and links, because simpy's authentication
    is handled via a redirect (302) to a login page. The HTTPRedirectHandler 
    implementation converts the POST request silently to a GET request, causing
    the request to lose all data, that should've been saved. 
    This handler fixes this problem by making the redirected request
    a POST request.
    
    see http://docs.python.org/lib/http-redirect-handler.html
    """
    def __init__(self, data):
        self.data = data
        
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        request = urllib2.HTTPRedirectHandler.redirect_request(self, req, fp, \
                                                               code, msg, headers, \
                                                               newurl)
        request.add_data(self.data)
        return request
        
        

##
## Data holding classes
##
        
class SimpyData(dict):
    """Base class that provides nice utility methods for data holding classes
    """
    def __init__(self, **kw):
        for k, v in self.args.iteritems(): self[k] = v            
        dict.__init__(self, kw)
        self.__dict__ = self
        
    def __str__(self):
        state = ["%s=%r" % (attribute, value) for (attribute, value) in self.__dict__.items()]
        return "\n".join(state).encode("utf-8") +"\n"     
        
    def acc(self):
        if self.accessType == "public": return 1
        else: return 0
        

        
class Link(SimpyData):
    """Data holder class for links 
    """
    args = {'title':'', 'url':'', 'note':'', 'nickname':'', \
            'accessType':'', 'addDateStr':'', 'tags':None, \
            'modDateStr':'', 'addDate':None, 'modDate':None}
            
    def __init__(self, **kw):
        SimpyData.__init__(self, **kw)
        if self.tags is None: self.tags = [] 
        
    def toPost(self):
        """
        """
        return {
            'title': self.title, 
            'href': self.url, 
            'note': self.note, 
            'urlNickname': self.nickname, 
            'tags': ','.join(self.tags),
            'accessType': self.acc()
        }
        
    def _validate(self):
        """
        """
        return bool(self.title and self.url and self.accessType)
    
        
        
class Note(SimpyData):
    """Data holder class for notes
    """
    args = {'title':'', 'uri':'', 'description':'', 'nickname':'', 'ident': '', \
            'accessType':'', 'addDateStr':'', 'tags':None, \
            'modDateStr':'', 'addDate':None, 'modDate':None}
            
    def __init__(self, **kw):
        SimpyData.__init__(self, **kw)
        if self.tags is None: self.tags = [] 
                
    def toPost(self):
        """
        """
        return {
            'title': self.title, 
            'id' : self.ident,
            'noteId' : self.ident,
            'description': self.description, 
            'tags': ','.join(self.tags) 
        }
        
    def _validate(self):
        """
        """
        return bool(self.title)    
        
        

class Watchlist(SimpyData):
    """Data holder class for a watchlist
    """
    args = {'identifier':'', 'name':'', 'description':'', 'newLinks':'', \
            'users': None, 'filters': None, 'addDate': None }
            
    def __init__(self, **kw):
        SimpyData.__init__(self, **kw)
        if self.users is None: self.users = [] 
        if self.filters is None: self.filters = [] 
                
    def toPost(self):
        """
        """
        return {}
        
    def _validate(self):
        """
        """
        return True    

    

##
## Utility functions 
##

def urlencode(params):
    """
    """
    data = ''
    if params is not None:
        for k, v in params.iteritems():
            data += '&'+ urllib.quote(k) +'='+ urllib.quote( v.encode('utf8')) 

    return data

    
    
def url(u):
    """constructs an absolute URL, out of the provided url, by prepending the 
    current BASE_URL 
    """
    return BASE_URL + u
    
    

def GET(url, user, passwd, params=None):
    """Performs GET request on url. Appends optional given 'params' as query params
    to URL. 
    Handles Basic Authentication and encoding of parameters.
    
    Return:
        Response body as string.
    """
    if params is None: params = {}
    auth = urllib2.HTTPBasicAuthHandler()
    auth.add_password(REALM, HOST, user, passwd)
    request = urllib2.Request(url +"?"+ urlencode(params))
    request.add_header('User-Agent', USER_AGENT)
    return urllib2.build_opener(auth).open(request).read()
    

    
def POST(url, user, passwd, params):
    """Performs a POST to the specified URL, 'params' are added to body of request. 
    Handles Basic Authentication and encoding of parameters.
    
    Return:
        Response body as string.
    """
    auth = urllib2.HTTPBasicAuthHandler()
    auth.add_password(REALM, HOST, user, passwd)
    data = urlencode(params)
    request = urllib2.Request(url)
    request.add_header('User-Agent', USER_AGENT)
    request.add_header('Content-type', 'application/x-www-form-urlencoded; UTF-8')
    request.add_data(data)
    return urllib2.build_opener(auth, PostRedirectHandler(data)).open(request).read()    

    

__compiledDateRE = re.compile("(\d{4})-(\d{2})-(\d{2})(\s(\d{2}):(\d{2}))?")

def parseSimpyDate(dateStr):
    """Parses a date string in the form 'YYYY-MM-DD' or 'YYYY-MM-DD HH:mm'.
    
    Return:
      A <date> or respectively a <datetime> object, depending on the 
      input. <None> if the provided string could not be parsed.
    """
    date = None
    m = __compiledDateRE.match(dateStr)
    if m is not None:
        groups = m.groups()
        if groups[3] is not None:
            date = datetime.datetime(int(groups[0]), int(groups[1]), int(groups[2]), \
                                     int(groups[4]), int(groups[5])) 
        else:
            date = datetime.date(int(groups[0]), int(groups[1]), int(groups[2]))
    return date



def parseTags(string):
    """Parses a response of the GetTags() call to the simpy API.
    
    Return:
      A list of dictionaries that contain 'count' int and a 'tag' string, 
      representing the list of tags that were returned by the API.
    """
    tags = []
    def start_element(name, attrs):
        if name == "tag":
            tags.append( {'count':int(attrs['count']), \
                          'tag':attrs['name'].encode("utf-8") } )
            
    parser = xml.parsers.expat.ParserCreate()
    parser.StartElementHandler = start_element
    parser.Parse( string )
    return tags
    
    
    
def parseWatchlists(string):
    """Parse a list of <watchlist> elements into a list of corresponding objects.
    """
    data = []
    def start_element(name, attrs):
        if name == "watchlist":
            data.append( Watchlist(  identifier = int(attrs['id']), \
                                     name = attrs['name'], \
                                     description = attrs['description'], \
                                     addDate = parseSimpyDate(attrs['addDate']), \
                                     newLinks = int(attrs['newLinks']) ) )
        elif name == "user":
            data[-1].users.append( attrs['username'] )
        elif name == "filter":
            data[-1].filters.append( { 'name': attrs['name'], 'query': attrs['query'] } )
        
    parser = xml.parsers.expat.ParserCreate()
    parser.StartElementHandler = start_element
    parser.Parse( string )
    return data    
    


def parseData(string):
    """Parse a list of <link> or <note> elements into a list of corresponding objects.
    """
    data = []
    tagstack = []
    def start_element(name, attrs):
        if name == "tag":
            data[-1].tags.append("")
        elif name == "link":
            data.append( Link( accessType=attrs['accessType'] ) )
        elif name == "note" and tagstack[-1] == "notes":    # be sure we are parsing notes
            data.append( Note( accessType=attrs['accessType'] ) )
            
        tagstack.append(name)
        
    def end_element(name):
        tagstack.pop()
        if name == "modDate": data[-1].modDate = parseSimpyDate(data[-1].modDateStr)
        elif name == "addDate": data[-1].addDate = parseSimpyDate(data[-1].addDateStr)
        
    def char_data(chardata):
        if tagstack[-1] == "title":         data[-1].title       += chardata
        elif tagstack[-1] == "url":         data[-1].url         += chardata
        elif tagstack[-1] == "uri":         data[-1].uri         += chardata
        elif tagstack[-1] == "id":          data[-1].ident       += chardata
        elif tagstack[-1] == "nickname":    data[-1].nickname    += chardata
        elif tagstack[-1] == "tag":         data[-1].tags[-1]    += chardata       
        elif tagstack[-1] == "addDate":     data[-1].addDateStr  += chardata       
        elif tagstack[-1] == "modDate":     data[-1].modDateStr  += chardata       
        elif tagstack[-1] == "description": data[-1].description += chardata       
        elif tagstack[-1] == "note" and isinstance(data[-1], Link):
            data[-1].note += chardata
        
    parser = xml.parsers.expat.ParserCreate()
    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    parser.CharacterDataHandler = char_data
    parser.Parse( string )
    return data    
    


def parseVoidResponse(string):
    """ Parse a response of a 'void' API call. These are mostly calls that 
    modify an entity on the server.
    A response looks like this:
        <status>
          <code>0</code>
          <message>Link saved successfully.</message>
        </status>
        
    Where the possible codes are:
        0: Success
        100: Required parameter missing
        200: Non-existent entity
        300: Transient entity retrieval error
        301: Entity storage error
        500: Storage quota reached
    
    Return:
      A dictionary that contains an 'code' int and a 'message' string, 
      representing the response. 
    """
    resp = {'codeStr':'', 'message':''}    
    tagstack = []
    def char_data(chardata):
        if tagstack[-1] == "message": resp['message'] += chardata 
        elif tagstack[-1] == "code":  resp['codeStr'] += chardata
        
    parser = xml.parsers.expat.ParserCreate()
    parser.StartElementHandler = lambda name, attrs: tagstack.append(name)
    parser.CharacterDataHandler = char_data
    parser.Parse( string )
    resp['code'] = int(resp['codeStr'])
    del resp['codeStr']
    return resp
        
  
    
##
## Calling the script from commandline?
## 

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        runtests = False
        for arg in sys.argv:
            if arg == 'runtests':
                runtests = True
                
        if runtests:
            sep = "\n\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++\n\n"
            c = SimpyClient('', '')
            print sep +"GET_WATCHLISTS\n\n"
            for l in c.getWatchlists(): print l
            print sep + "GET_LINKS\n\n"
            for l in c.getLinks(): print l
            print sep +"GET_TAGS\n\n"
            for t in c.getTags(): print t
            for t in c.getTags(3): print t
            print sep + "REMOVE_TAG\n\n"
            print c.removeTag('please delete this one') 
            print sep + "RENAME_TAG\n\n"
            print c.renameTag('@to_delete', 'please keep em') 
            print sep + "MERGE_TAGS\n\n"
            print c.mergeTags('mergetag1', 'mergetag2', 'tag merge target') 
            print sep + "SPLIT_TAG\n\n"
            print c.splitTag('please split me now', 'splitted1', 'splitted2') 
            print sep +"SAVE_NOTE\n\n"
            print c.saveNote( Note( title='test note title', description='test note description', tags=['@fortestonly']) )
            print sep +"GET_NOTES\n\n"
            testnotes = c.getNotes( query='tags:@fortestonly' )
            for t in testnotes: print t
            print sep +"DELETE_NOTES\n\n"
            for t in testnotes: print c.deleteNote(t)
    else:
        print __doc__
        sys.exit(0)
