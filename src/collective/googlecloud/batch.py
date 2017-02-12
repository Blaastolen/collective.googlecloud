import sys
import argparse
import transaction
from transaction import get
from logging import getLogger
from Testing import makerequest
from zope.site.hooks import setHooks
from zope.site.hooks import setSite
from AccessControl.SecurityManagement import newSecurityManager
from plone.dexterity.interfaces import IDexterityItem
from plone.scale.storage import AnnotationStorage
from plone.app.folder.utils import checkpointIterator
from plone.app.folder.utils import timer
from time import clock
from time import strftime
from zExceptions import NotFound

def mklog(request):
    """ helper to prepend a time stamp to the output """
    write = request.RESPONSE.write

    def log(msg, timestamp=True, cr=True):
        if timestamp:
            msg = strftime('%Y/%m/%d-%H:%M:%S ') + msg
        if cr:
            msg += '\n'
        write(msg)
    return log


def reset_scales(app, args):
    parser = argparse.ArgumentParser(description='Reset all scales in the application')
    parser.add_argument('--site', help='Add the site id', required=True)
    parser.add_argument('--regenerate', help='Scale(s) you want to regnerate, multiple allowed', action='append')
    parser.add_argument('-c', help='stupid bug')
    args = parser.parse_args(args)
    site_name = args.site

    root = makerequest.makerequest(app)
    site = root.get(site_name, None)

    logger = getLogger(__name__)
    log = mklog(root.REQUEST)
    if site is None:
        msg = "No site called `%s` found in the database." % site_name
        log(msg)
        logger.info(msg)
        sys.exit(1)

    # Set up local site manager
    setHooks()
    setSite(site)

    # Set up security
    uf = app.acl_users
    user = uf.getUserById("admin")
    newSecurityManager(None, user)
    catalog = site.portal_catalog
    
    log('resetting all scales from %r:' % site)
    real = timer()          # real time
    lap = timer()           # real lap time (for intermediate commits)
    cpu = timer(clock)      # cpu time
    processed = 0
    def checkPoint():
        msg = 'intermediate commit '\
            '(%d objects processed, last batch in %s)...'
        log(msg % (processed, lap.next()))
        trx = get()
        trx.note(u'migrated %d btree-folders' % processed)
        trx.savepoint()
    cpi = checkpointIterator(checkPoint, 1000)
    for item in catalog(object_provides=IDexterityItem.__identifier__):
        o = item.getObject()
        storage = AnnotationStorage(o)
        storage.clear()
        msg = "Cleared storage for %s" % (item.getURL())
        log(msg)

        try:
            if args.regenerate is not None:
                for scale in args.regenerate:
                    if hasattr(o,'image'):
                        scaler = o.unrestrictedTraverse('@@images')
                        if scaler.scale(fieldname='image', scale=scale) is not None:
                            log("regenerated scale  %s" % (scale))
                        else:
                            log("error regenerating scale  %s" % (scale))
        except AttributeError:
            continue
        except IOError:
            continue
        processed += 1
        cpi.next()
    checkPoint() 
    msg = 'processed %d object(s) in %s (%s cpu time).'
    msg = msg % (processed, real.next(), cpu.next())
    log(msg)
    logger.info(msg)
    transaction.commit()
    
    