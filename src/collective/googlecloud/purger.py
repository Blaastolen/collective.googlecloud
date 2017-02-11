# -*- coding: utf-8 -*-
"""
Google purger. Will call out to the gcloud command to purge cdn cache.
"""
import subprocess
import urlparse

from plone.cachepurging.interfaces import IPurger
from zope.interface import implementer

from collective.googlecloud import GOOGLE_LOAD_BALANCER

@implementer(IPurger)
class GooglePurger(object):

    def __init__(self, factory=None, timeout=30, backlog=200,
                 errorHeaders=('x-squid-error', ), http_1_1=True):
        pass

    def purgeAsync(self, url, httpVerb='PURGE'):
        """
        Purge asyncronosly. This is very slow.
        """
        (scheme, host, path, params, query, fragment) = urlparse.urlparse(url)
        subprocess.call(["gcloud", "compute", "url-maps", "invalidate-cdn-cache",
                         GOOGLE_LOAD_BALANCER, "-path", path, "--host", host, "--async"])

        return

    def purgeSync(self, url, httpVerb='PURGE'):
        """
        Purge syncronosly. This is very slow.
        """
        (scheme, host, path, params, query, fragment) = urlparse.urlparse(url)
        purge = subprocess.Popen(["gcloud", "compute", "url-maps", "invalidate-cdn-cache",
                                  GOOGLE_LOAD_BALANCER, "-path", path, "--host", host],
                                 stdout=subprocess.PIPE)
        output, err = purge.communicate()
        return "200", output, err

    def stopThreads(self, wait=False):
        """
        As we call out to external command for purging, this does not make much sense
        """
        return True

GOOGLE_PURGER = GooglePurger()
