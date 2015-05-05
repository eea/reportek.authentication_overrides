# python
from xml.dom import minidom as minidom

# zope
import transaction

from anz.casclient.principal import Principal
from anz.casclient.assertion import Assertion
from anz.casclient.proxyretriever import Cas20ProxyRetriever
from anz.casclient.exceptions import TicketValidationException


def reportek_parseResponseFromServer( self, response ):
    ''' See interfaces.ITicketValidator. '''
    try:
        dom = minidom.parseString( response )
        elements = dom.getElementsByTagNameNS( self.CAS_NS,
                                               'authenticationFailure' )
        if elements:
            raise TicketValidationException( elements[0].firstChild.data )
        
        elements = dom.getElementsByTagNameNS( self.CAS_NS, 'user' )
        userId = elements and elements[0].firstChild.data or None
        if not userId:
            raise TicketValidationException(
                'No principal was found in the response.' )

        elements = dom.getElementsByTagNameNS( self.CAS_NS,
                                               'proxyGrantingTicket' )
        pgtIouNode = elements and elements[0] or None
        if pgtIouNode:
            pgtIou = pgtIouNode.firstChild.data

            # Explicite call transaction.begin() to sync invalidations
            # for a given transaction, make sure to get the latest pgt
            # storage data. This will be a issue when anz.cas and
            # anz.casclient deploied on the same zope instance.
            transaction.begin()

            pgt = self.pgtStorage.retrieve( pgtIou )
            if pgt:
                principal = Principal(
                    userId, pgt,
                    Cas20ProxyRetriever(self.casServerUrlPrefix) )
            else:
                raise TicketValidationException(
                    'No pgt found for pgtIou %s.' % pgtIou )
        else:
            principal = Principal( userId )

        return Assertion( principal )
    except Exception, e:
        raise ValueError( str(e) )
