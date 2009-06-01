#!/usr/bin/env python
import sys, datetime, urllib2 # Standard library stuff.
import web # web.py
sys.path.append('./markdown-1.7')
from markdown import Markdown
sys.path.append('./simpyapi-python-1.1')
from simpy import SimpyClient
import config # the config file

# Utility functions
# =================

def markdown(text):
    """Given a string of plain text, return a string of html via markdown."""
    md = Markdown()
    return md.convert(text)

class SimpyLink:
    """A link from a simpy account."""
    
    def __init__(self,d):

        self.d = d
        
        # Prefer to use the nickname, but if it's empty fall back on the 
        # title.
        if d['nickname'] == '':
            self.name = web.safestr(d['title'])
        else:
            self.name = web.safestr(d['nickname'])
        self.note = d['note']
        self.note_html = markdown(self.note)
        self.tags = d['tags']
        self.date = d['addDate']
        self.datestr = web.datestr(self.date)
        self.url = d['url']
        i = len(self.url)
        try:
            i = self.url.index('?')
        except ValueError:
            # url does not contain a '?'
            pass            
        self.permalink = self.url[0:i]
        template = web.template.frender('templates/simpylink.html')
        self.html = template(self)
        
# The simpy stuff
# ===============

# Initialise the SimpyClient object that handles accessing simpy.
simpy = SimpyClient(config.simpy_user,config.simpy_pass)

# Queries used to get lists of links from query.
UNREAD_QUERY = '+tags:"read later" -tags:"have read"'
STARRED_QUERY = '+tags:starred'
READ_QUERY = '+tags:"have read"'

class SimpyNotAvailableError(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def getLinks(query):
    """Return all the links from simpy that match a given query as a list of
    SimpyLink objects."""
    try:
        links = simpy.getLinks({'limit':'-1','q':query})
    except urllib2.HTTPError, e:
        raise SimpyNotAvailableError(e)
    link_objects = []
    for link in links:
        link_objects.append(SimpyLink(link))
    return link_objects

def getUnread():
    """Return all the links from simpy that have the tag 'read later' but do
    not have the tag 'have read'."""
    return getLinks(UNREAD_QUERY)

def getStarred():
    """Return all the links from simpy that have either the 'read later' or
    'have read' (or both) _and_ the starred tag."""
    return getLinks(STARRED_QUERY)

def getRead():
    """Return all the links from simpy that have the 'have read' tag."""
    return getLinks(READ_QUERY)
    
# The web.py stuff
# ================

# Tell web.py to look for templates in the templates/ directory, and use 
# base.html as the base template in which all other templates are wrapped.
# globals_opts is a dictionary of variables available to all templates.
global_opts = {'title':config.title,'base_url':config.base_url,'user':config.simpy_user, 'unread_query':UNREAD_QUERY,'starred_query':STARRED_QUERY,'read_query':READ_QUERY}
render = web.template.render('templates/', base='base', globals=global_opts)

# Specify URLs to web.py.
urls = (
  '/?', 'UnreadPage',
  '/starred', 'StarredPage',
  '/read', 'ReadPage',
  '/link/(.*)', 'LinkPage',
  '/about', 'AboutPage'
)
app = web.application(urls,globals())

class UnreadPage:
    """Shows all the unread links."""
    def GET(self):
        return render.unread(getUnread())

class ReadPage:
    """Shows all the read links."""
    def GET(self):
        return render.read(getRead())

class StarredPage:
    """Shows all the starred links (read or unread)."""
    def GET(self):
        return render.starred(getStarred())
    
class AboutPage:
    """Page that shows the site's about text."""
    def GET(self):
        text = open("README.mkdwn").read()
        html = markdown(text)
        return render.about(html)

if __name__ == "__main__":
    web.config.debug = True
    app.run()
