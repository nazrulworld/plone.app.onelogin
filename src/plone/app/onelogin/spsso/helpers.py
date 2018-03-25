# -*- coding: utf-8 -*-
# @Date    : 2018-03-24 14:49:42
# @Author  : Md Nazrul Islam (email2nazrul@gmail.com)
# @Link    : http://nazrul.me/
# @Version : $Id$
# All imports here
from .setting import SAML_BASE_PATH
from DateTime import DateTime
from plone import api
from plone.api.validation import required_parameters
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from six.moves.urllib.parse import urlparse


__author__ = 'Md Nazrul Islam (email2nazrul@gmail.com)'

SAML_DATA_SESSION_KEY = 'SAML_DATA'

@required_parameters('request_data')
def init_saml_auth(request_data):
    """ """
    auth = OneLogin_Saml2_Auth(request_data, custom_base_path=SAML_BASE_PATH)
    return auth


@required_parameters('request')
def prepare_request_data(request):

    url_data = urlparse(request.getURL())
    return {
        'https': 'on' if url_data.scheme == 'https' else 'off',
        'http_host': request.getHeader('HTTP_HOST'),
        'server_port': request.getHeader('SERVER_PORT'),
        'script_name': request.getHeader('PATH_INFO'),
        'get_data': request.form.copy(),
        'post_data': request.form.copy(),
        # Uncomment if using ADFS as IdP, https://github.com/onelogin/python-saml/pull/144
        # 'lowercase_urlencoding': True,
        'query_string': request.getHeader('QUERY_STRING')
    }


@required_parameters('request')
def make_sso_challange(request):
    """ """
    request_data = prepare_request_data(request)
    auth = init_saml_auth(request_data)

    rely_state = request.get('came_from', None)

    if rely_state is None:
        rely_state = request.get('ACTUAL_URL', api.portal.get_tool('portal_url')())
        query = request_data.get('query_string')
        if query:
            if not query.startswith('?'):
                query = '?' + query
            rely_state = rely_state + query

    return auth.login(rely_state)


@required_parameters('request')
def process_saml_response(request):
    """ """
    request_data = prepare_request_data(request)
    auth = init_saml_auth(request_data)

    auth.process_response()
    errors = auth.get_errors()
    is_authenticated = auth.is_authenticated()

    data = dict()
    if len(errors) == 0:
        data['samlUserdata'] = auth.get_attributes()
        data['samlNameId'] = auth.get_nameid()
        data['samlSessionIndex'] = auth.get_session_index()
        data['samlSessionExpire'] = auth.get_session_expiration()

    return is_authenticated, is_authenticated and data or errors


@required_parameters('data')
def set_saml_session_data(data):
    """ """
    sdm = api.portal.get_tool('session_data_manager')
    session = sdm.getSessionData(create=True)
    session[SAML_DATA_SESSION_KEY] = data

def clean_saml_session_data():
    """ """
    session_manager = context.session_data_manager
    if not session_manager.hasSessionData():
        return

    session = session_manager.getSessionData()
    if session.has_key(SAML_DATA_SESSION_KEY):
        del session[SAML_DATA_SESSION_KEY]

