# -*- coding: utf-8 -*-
from uuid import uuid4
from google.cloud.storage import Client
from google.cloud.storage import Blob
from google.cloud.exceptions import NotFound
from plone.scale.storage import AnnotationStorage
from plone.namedfile.utils import set_headers
from plone.namedfile.utils import stream_data

import httplib2shim
httplib2shim.patch()

from collective.googlecloud import GOOGLE_STORAGE_BUCKET

BUCKET = Client().get_bucket(GOOGLE_STORAGE_BUCKET)
KEEP_SCALE_MILLIS = 24 * 60 * 60 * 1000

#  patches for
#  plone.namedfile.scaling.ImageScale

def patched___init__(self, context, request, **info):
    self.context = context
    self.request = request
    self.__dict__.update(**info)
    if self.data is None:
        self.data = getattr(self.context, self.fieldname)

    url = self.context.absolute_url()
    extension = self.data.contentType.split('/')[-1].lower()
    if 'uid' in info:
        name = info['uid']
    else:
        name = info['fieldname']
    self.__name__ = u'{0}.{1}'.format(name, extension)
    self.url = u'{0}/@@images/{1}'.format(url, self.__name__)
    #patched part, rest is oriniganl
    if 'google_url' in info:          #added line
        self.url = info['google_url'] #added line
        self.google_url = self.url    #added line
    else:                             #parched line
        self.google_url = None        #added line


def patched_index_html(self):
    """ download the image """
    self.validate_access()
    if getattr(self, 'google_url', None) is not None: #parched line
        response = self.request.response #parched line
        response.redirect(getattr(self, 'google_url'), lock=True) #parched line
        return '' #parched line
    set_headers(self.data, self.request.response)
    return stream_data(self.data)


def patched_HEAD(self, REQUEST, RESPONSE=None):
    """ Obtain metainformation about the image implied by the request
    without transfer of the image itself
    """
    self.validate_access()
    if getattr(self, 'google_url', None) is not None: #parched line
        response = self.request.response #parched line
        response.redirect(getattr(self, 'google_url'), lock=True) #parched line
        return '' #parched line

    set_headers(self.data, REQUEST.response)
    return ''


#  patches for
#  plone.scale.storage.AnnotationStorage

def patched_scale(self, factory=None, **parameters):
    key = self.hash(**parameters)
    storage = self.storage
    info = self.get_info_by_hash(key)
    if info is not None and self._modified_since(info['modified']):
        del storage[info['uid']]
        # invalidate when the image was updated
        info = None
    if info is None and factory:
        result = factory(**parameters)
        if result is not None:
            # storage will be modified:
            # good time to also cleanup
            #self._cleanup() # commented line
            data, format, dimensions = result
            width, height = dimensions
            uid = str(uuid4())
            gblob = Blob(uid, BUCKET) #added line
            blob = data.open('r') #added line
            gblob.upload_from_file(blob) #added line
            blob.close() #added line
            gblob.make_public() #added line
            google_url = gblob.public_url #added line
            del data #added line
            info = dict(uid=uid, data=None, width=width, height=height, #patched line s,data=data,data=None
                        mimetype='image/%s' % format.lower(), key=key,
                        modified=self.modified_time, google_url=google_url) #patched line, added google_url
            storage[uid] = info
    return info


def patched_clear(self):
    storage = self.storage          #added line
    for key, value in storage.items(): #added line
        try:                        #added line
            BUCKET.delete_blob(key) #added line
        except NotFound:            #added line
            pass                    #added line

    self.storage.clear()


def patched__cleanup(self):
    storage = self.storage
    modified_time = self.modified_time
    for key, value in storage.items():
        # remove info stored by tuple keys
        # before refactoring
        if isinstance(key, tuple):
            del storage[key]
        # clear cache from scales older than one day
        elif (modified_time and
                value['modified'] < modified_time - KEEP_SCALE_MILLIS):
            del storage[key]
            try:                        #added line
                BUCKET.delete_blob(key) #added line
            except NotFound:            #added line
                pass                    #added line

def object_modified_or_deleted(obj, event):
    storage = AnnotationStorage(obj)
    storage.clear()