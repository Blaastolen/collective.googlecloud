import sys
import transaction
import argparse
from Testing import makerequest
from zope.site.hooks import setHooks
from zope.site.hooks import setSite
from AccessControl.SecurityManagement import newSecurityManager
from plone.dexterity.interfaces import IDexterityItem
from plone.scale.storage import AnnotationStorage

def reset_scales(app, args):

    parser = argparse.ArgumentParser(description='Reset all scales in the application')
    parser.add_argument('--site', help='Add the site id', required=True)
    parser.add_argument('-c', help='stupid bug')
    args = parser.parse_args(args)
    site_name = args.site

    root = makerequest.makerequest(app)
    site = root.get(site_name, None)


    if site is None:
        print "No site called `%s` found in the database." % site_name
        sys.exit(1)

    # Set up local site manager
    setHooks()
    setSite(site)

    # Set up security
    uf = app.acl_users
    user = uf.getUserById("admin")
    newSecurityManager(None, user)
    catalog = site.portal_catalog
    for item in catalog(object_provides=IDexterityItem.__identifier__):
        storage = AnnotationStorage(item.getObject())
        storage.clear()
    transaction.commit()
    
    