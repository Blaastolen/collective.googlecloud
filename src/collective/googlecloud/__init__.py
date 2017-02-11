# -*- coding: utf-8 -*-
"""Init and utils."""

import os
from zope.i18nmessageid import MessageFactory

GOOGLE_STORAGE_BUCKET = None
GOOGLE_LOAD_BALANCER = None

if os.getenv('GOOGLE_STORAGE_BUCKET'):
    GOOGLE_STORAGE_BUCKET = os.getenv('GOOGLE_STORAGE_BUCKET')
if os.getenv('GOOGLE_LOAD_BALANCER'):
    GOOGLE_LOAD_BALANCER = os.getenv('GOOGLE_LOAD_BALANCER')

if GOOGLE_STORAGE_BUCKET is None or GOOGLE_LOAD_BALANCER is None:
    raise Exception("""
    GOOGLE_STORAGE_BUCKET and GOOGLE_LOAD_BALANCER are mandatory. 
    Please add them to your instance section of the buildout
    
    environment-vars =
        GOOGLE_STORAGE_BUCKET 'storagebucket name' #(not including the gs:// part)
        GOOGLE_LOAD_BALANCER 'name of the load balancer'
    """)


_ = MessageFactory('collective.googlecloud')
