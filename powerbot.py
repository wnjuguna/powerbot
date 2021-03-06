#!/usr/bin/env python

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch import InvalidURLError, DownloadError
from urllib import urlencode
import re
import os
import jinja2

JINJA2_ENVIRONMENT = jinja2.Environment(
        loader = jinja2.loaders.FileSystemLoader(
            [os.path.dirname('__file__')]),
        extensions = ['jinja2.ext.autoescape'],
        autoescape = True)

class Notice(ndb.Model):
    """
    NDB entity model
    """
    date = ndb.DateProperty()
    duration = ndb.StringProperty()
    town = ndb.StringProperty()
    neighbourhood = ndb.TextProperty()

class PowerAlert(object):
    def __init__(self):
        """
        Initialize object
        """
        self.url = "http://poweralerts.kenyapower.co.ke"
        return

    def fetchPage(self):
        """
        Fetch poweralerts page
        """
        try:
            res = urlfetch.Fetch(self.url).content
        except (InvalidURLError, DownloadError), e:
            raise(e)
        else:
            return res

    def crawlPage(self):
        """
        Extract notices from page.
        """
        page = self.fetchPage()
        page = re.sub('For more info visit|www.kplc.co.ke', '', page)
        soup = BeautifulSoup(page, 'html.parser')
        for notice in soup.find_all(class_='ScheduleHeader'):
            location = []
            d = datetime.now().strftime('%Y') +' '+re.search(', (\d+ \w+) ',
                    notice.text).group(1)
            date = datetime.strptime(d, '%Y %d %b')
            duration = re.search(', \d+ \w+ (.*)$', notice.text).group(1)
            duration = re.sub('\(\w.+\)', '', duration).strip()
            for string in notice.nextSibling.stripped_strings:
                location.append(string)

            hoods = ','.join(location[1:])
            key_name = str(hash((date,hoods)))
            try:
                Notice.get_or_insert(key_name,
                        date = date,
                        town = location[0],
                        duration = duration,
                        neighbourhood = hoods)
            except Exception, e:
                print "%s" %(e)
        return

    @property
    def notices(self):
        """
        Query DB for scheduled outages for today and tomorrow
        """
        date = datetime.today()
        today = datetime(date.year, date.month, date.day)
        tomorrow = today + timedelta(days=1)
        try:
            cursor = Notice.query(Notice.date > today, Notice.date <= tomorrow)
        except Exception, e:
            print "Unable to query DB: %s" %(e)
        else:
            alerts = []
            for notice in cursor:
                town = notice.town
                date = notice.date.strftime('%A, %b %d')
                duration = notice.duration
                hood = notice.neighbourhood
                alerts.append({
                    'town': town,
                    'date': date,
                    'duration': duration,
                    'hood': hood })

            template_vars = {'alerts': alerts}
            template = JINJA2_ENVIRONMENT.get_template('telegram.j2')
            telegram = template.render(template_vars)
            template = JINJA2_ENVIRONMENT.get_template('facebook.j2')
            facebook = template.render(template_vars)
            return facebook, telegram
