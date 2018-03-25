# -*- coding: utf-8 -*-
from AccessControl.SecurityInfo import ClassSecurityInfo
from plone import api
from plone.app.onelogin.interfaces import IOneloginSSOPlugin
from plone.app.onelogin.spsso.helpers import clean_saml_session_data
from plone.app.onelogin.spsso.helpers import make_sso_challange
from plone.app.onelogin.spsso.helpers import process_saml_response
from plone.app.onelogin.spsso.helpers import set_saml_session_data
from plone.app.onelogin.spsso.helpers import SAML_DATA_SESSION_KEY
from plone.session.plugins.session import SessionPlugin
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin
from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin
from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin
from Products.PluggableAuthService.interfaces.plugins import ICredentialsResetPlugin
from zope.interface import implementer_only
from zope.interface import Invalid

import binascii
import six
import sys
import time


__author__ = 'Md Nazrul Islam<email2nazrul@gmail.com>'

PLUGIN_ID = 'onelogin_sso'
PLUGIN_TITLE = 'Onelogin SSO authentication'

manage_addOneloginSSOPluginForm = PageTemplateFile('add_plugin', globals())


def manage_addOneloginSSOPlugin(dispatcher, id, title=None, path='/', REQUEST=None):
    """Add a onelogin sso plugin."""

    plugin = OneloginSSOPlugin(id, title=title, path=path)
    dispatcher._setObject(id, plugin)

    if REQUEST is not None:
        REQUEST.response.redirect(
            '{0}/manage_workspace?'
            'manage_tabs_message=Onelogin+SSO+plugin+created.'.format(
                dispatcher.absolute_url()
            )
        )


@implementer_only(
    IOneloginSSOPlugin,
    IAuthenticationPlugin,
    IChallengePlugin,
    IExtractionPlugin,
    ICredentialsResetPlugin
)
class OneloginSSOPlugin(SessionPlugin):
    """Onelogin SSO Plugin that is derived from Session authentication plugin.
    It is also remarkable that update credential is disabled for PAS, it will internally be
    handled.
    """
    meta_type = 'Onelogin SSO Plugin'
    cookie_name = '__onelogin_saml'
    extractor_name = 'plone.app.onelogin'
    security = ClassSecurityInfo()

    def __init__(self, id, title=None, path='/'):
        """ """
        self._setId(id)
        self.title = title
        self.path = path

    @security.private
    def challenge(self, request, response, **kw):
        """ Challenge the user for credentials. """

        if request.get(self.cookie_name, None):
            # if we have the saml cookie, we are already logged
            # in, and we should not challenge - a challenge
            # would create a loop.
            return False

        url = make_sso_challange(request)

        response.redirect(url, lock=1)
        response.setHeader('Expires', 'Sat, 01 Jan 2000 00:00:00 GMT')
        response.setHeader('Cache-Control', 'no-cache')
        return True

    @security.private
    def extractCredentials(self, request):
        """IExtractionPlugin implementation, overridden """
        creds = {}
        if self.cookie_name in request:
            try:
                creds['cookie'] = binascii.a2b_base64(
                    request.get(self.cookie_name)
                )
                creds['source'] = 'plone.app.onelogin'
            except binascii.Error as exc:
                # If we have a cookie which is not properly base64 encoded it
                # can not be ours.
                if api.env.debug_mode():
                    six.reraise(Invalid, Invalid(str(exc)), sys.exc_info()[2])
                else:
                    return creds

        if request.method == 'POST' and 'SAMLResponse' in request.form.keys():
            # onelogin SAML ACS(Assertion Consumer Service)
            is_valid, response = process_saml_response(request)
            if not is_valid:
                return creds

            creds['login'] = response.get('samlNameId')
            creds['saml_data'] = response
            creds['source'] = 'plone.app.onelogin'

        return creds

    def authenticateCredentials(self, credentials):
        """IAuthenticationPlugin implementation """
        if not credentials.get("source", None) == 'plone.app.onelogin':
            return None

        login_step = False
        pas = self._getPAS()

        if 'cookie' in credentials.keys():
            ticket = credentials['cookie']
            ticket_data = self._validateTicket(ticket)
            if ticket_data is None:
                return None
            (digest, userid, tokens, user_data, timestamp) = ticket_data
            info = pas._verifyUser(pas.plugins, user_id=userid)

        elif 'login' in credentials.keys():
            login_step = True
            username = credentials.get('login', '').encode('utf-8')
            info = pas._verifyUser(pas.plugins, login=username)

        else:
            # Bad request!!!
            return None

        if info is None:
            return None

        # further validation?

        if login_step:
            # login stage!
            self.REQUEST[SAML_DATA_SESSION_KEY] = credentials['saml_data']

        return (info['id'], info['login'])

    def updateCredentials(self, request, response, login, new_password):
        """Cannot called by PAS, need manually called"""
        pas = self._getPAS()
        info = pas._verifyUser(pas.plugins, login=login)

        if info is not None and SAML_DATA_SESSION_KEY in self.REQUEST:

            original_cookie_lifetime = self.cookie_lifetime

            saml_data = self.REQUEST[SAML_DATA_SESSION_KEY]
            if 'samlSessionExpire' in saml_data.keys():
                # tiny hack
                interval = int(saml_data['samlSessionExpire']) - int(time.time())
                self.cookie_lifetime = interval / (24 * 60 * 60)

            self._setupSession(info['id'], response)

            # need to run as manager?
            set_saml_session_data(saml_data)

            # restore original
            self.cookie_lifetime = original_cookie_lifetime
        else:
            print "Invalid request!"

    def resetCredentials(self, request, response):
        """ """
        super(OneloginSSOPlugin, self).resetCredentials(request, response)

        clean_saml_session_data()
