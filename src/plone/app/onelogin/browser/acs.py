# -*- coding: utf-8 -*-
# @Date    : 2018-03-22 15:08:37
# @Author  : Md Nazrul Islam (nazrul@zitelab.dk)
# @Link    : http://nazrul.me/
# @Version : $Id$
# All imports here
from DateTime import DateTime
from plone import api
from plone.app.onelogin.spsso.helpers import init_saml_auth
from plone.app.onelogin.spsso.helpers import prepare_request_data
from plone.app.onelogin.spsso.pas.plugin import PLUGIN_ID
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


__author__ = 'Md Nazrul Islam (nazrul@zitelab.dk)'


class Challange(BrowserView):
    """ """
    def __call__(self):
        """ """
        request_data = prepare_request_data(self.request)
        auth = init_saml_auth(request_data)
        self.request.response.redirect(auth.login(self.context.absolute_url()), lock=1)


class AssertionConsumerService(BrowserView):

    """ """
    index = ViewPageTemplateFile('acs.pt')

    def __call__(self):
        """" """
        is_auth = self.authenticate()

        if is_auth:
            request_data = prepare_request_data(self.request)
            auth = init_saml_auth(request_data)
            api.portal.show_message('You have successfully logged in through Onelogin', self.request)

            success_url = request_data['post_data'].get('RelayState', api.portal.get_tool('portal_url')())
            self.request.response.redirect(auth.redirect_to(success_url), lock=1)

        else:
            api.portal.show_message('There was error authentication through Onelogin', self.request, 'error')
            return self.index()

    def authenticate(self):
        """ """
        membership_tool = api.portal.get_tool('portal_membership')
        if membership_tool.isAnonymousUser():
            return False

        member = membership_tool.getAuthenticatedMember()
        login_time = member.getProperty('login_time', '2000/01/01')
        if not isinstance(login_time, DateTime):
            login_time = DateTime(login_time)
        initial_login = int(login_time == DateTime('2000/01/01'))
        print initial_login

        # update session
        self.get_sso_pas_plugin().updateCredentials(
            self.request,
            self.request.response,
            member.getUserName(),
            ''
        )
        membership_tool.loginUser(self.request)

        return True

    def get_sso_pas_plugin(self):
        """ """
        uf = api.portal.get_tool('acl_users')
        return uf[PLUGIN_ID]
