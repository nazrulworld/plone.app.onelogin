# -*- coding: utf-8 -*-
# @Date    : 2018-03-22 15:08:37
# @Author  : Md Nazrul Islam (nazrul@zitelab.dk)
# @Link    : http://nazrul.me/
# @Version : $Id$
# All imports here
from plone import api
from plone.app.onelogin.spsso.helpers import init_saml_auth
from plone.app.onelogin.spsso.helpers import prepare_request_data
from Products.Five.browser import BrowserView
from zExceptions import BadRequest


__author__ = 'Md Nazrul Islam (nazrul@zitelab.dk)'


class ServiceProviderMetaData(BrowserView):

    """ """
    def __call__(self):
        """" """
        request_data = prepare_request_data(self.request)

        auth = init_saml_auth(request_data)

        settings = auth.get_settings()

        metadata = settings.get_sp_metadata()

        errors = settings.validate_metadata(metadata)

        self.request.response.setHeader('Content-Type', 'application/xml')

        if len(errors) == 0:
            return metadata

        raise BadRequest(', '.join(errors))
