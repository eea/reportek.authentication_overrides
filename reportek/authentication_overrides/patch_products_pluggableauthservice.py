from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin
from Products.PluggableAuthService.PluggableAuthService import _SWALLOWABLE_PLUGIN_EXCEPTIONS
from Products.PluggableAuthService.PluggableAuthService import logger
from Products.PluggableAuthService.PluggableAuthService import reraise
from Products.PluggableAuthService.PluggableAuthService import DumbHTTPExtractor
from Products.PluggableAuthService.utils import createViewName
from Products.PluggableAuthService.utils import createKeywords


def _reportek_extractUserIds( self, request, plugins ):

    """ request -> [ validated_user_id ]

    o For each set of extracted credentials, try to authenticate
      a user;  accumulate a list of the IDs of such users over all
      our authentication and extraction plugins.
    """
    try:
        extractors = plugins.listPlugins( IExtractionPlugin )
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        logger.debug('Extractor plugin listing error', exc_info=True)
        extractors = ()

    if not extractors:
        extractors = ( ( 'default', DumbHTTPExtractor() ), )

    try:
        authenticators = plugins.listPlugins( IAuthenticationPlugin )
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        logger.debug('Authenticator plugin listing error', exc_info=True)
        authenticators = ()

    result = []

    for extractor_id, extractor in extractors:

        try:
            credentials = extractor.extractCredentials( request )
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            reraise(extractor)
            logger.debug( 'ExtractionPlugin %s error' % extractor_id
                        , exc_info=True
                        )
            continue

        if credentials:

            try:
                credentials[ 'extractor' ] = extractor_id # XXX: in key?
                # Test if ObjectCacheEntries.aggregateIndex would work
                items = credentials.items()
                items.sort()
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                # XXX: would reraise be good here, and which plugin to ask
                # whether not to swallow the exception - the extractor?
                logger.debug( 'Credentials error: %s' % credentials
                            , exc_info=True
                            )
                continue

            # First try to authenticate against the emergency
            # user and return immediately if authenticated
            user_id, name = self._tryEmergencyUserAuthentication(
                                                        credentials )

            if user_id is not None:
                return [ ( user_id, name ) ]

            # Now see if the user ids can be retrieved from the cache
            credentials['login'] = self.applyTransform( credentials.get('login') )
            view_name = createViewName('_extractUserIds',
                                       credentials.get('login'))
            keywords = createKeywords(**credentials)
            user_ids = self.ZCacheable_get( view_name=view_name
                                          , keywords=keywords
                                          , default=None
                                          )
            if user_ids is None:
                user_ids = []

                for authenticator_id, auth in authenticators:

                    try:
                        uid_and_info = auth.authenticateCredentials(
                            credentials )

                        if uid_and_info is None:
                            continue

                        user_id, info = uid_and_info

                    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                        reraise(auth)
                        msg = 'AuthenticationPlugin %s error' % (
                                authenticator_id, )
                        logger.debug(msg, exc_info=True)
                        continue

                    if user_id is not None:
                        user_ids.append( (user_id, info) )

                if user_ids:
                    self.ZCacheable_set( user_ids
                                       , view_name=view_name
                                       , keywords=keywords
                                       )

            result.extend( user_ids )

    # Emergency user via HTTP basic auth always wins
    user_id, name = self._tryEmergencyUserAuthentication(
            DumbHTTPExtractor().extractCredentials( request ) )

    if user_id is not None:
        return [ ( user_id, name ) ]

    return result
