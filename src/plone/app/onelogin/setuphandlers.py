# -*- coding: utf-8 -*-
from Acquisition import aq_parent
from plone import api
from plone.app.onelogin.spsso.pas.plugin import manage_addOneloginSSOPlugin
from plone.app.onelogin.spsso.pas.plugin import PLUGIN_ID
from plone.app.onelogin.spsso.pas.plugin import PLUGIN_TITLE
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer

import logging


__author__ = 'Md Nazrul Islam<email2nazru@gmail.com>'

logger = logging.getLogger('plone.app.onelogin')


@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            'plone.onelogin:uninstall',
        ]


def set_plugin_position(uf, interface_name, position=None):
        """ """
        plugin_interface = uf.plugins._getInterfaceFromName(interface_name)
        plugins_count = len(uf.plugins.listPlugins(plugin_interface))
        if position is None:
            # By Default just last second postion
            position = plugins_count - 2
            if position < 0:
                position = 0
        else:
            if position > (plugins_count - 1):
                raise IndexError('Your position number `{0}` is out of index!'.format(position))

        while uf.plugins.listPlugins(plugin_interface)[position][0] != PLUGIN_ID:
            uf.plugins.movePluginsUp(plugin_interface, [PLUGIN_ID, ])


def install_pas_plugin(portal):
    """ """
    """ This plugin needs to be installed in two places, the instance PAS where
    logins occur and the root acl_users.

    Different interfaces need to be activated for either case.
    """
    logger.info('Installing plone.app.onelogin:{0}'.format(PLUGIN_ID))

    uf = api.portal.get_tool('acl_users')

    # define the interfaces which need to be activated for either PAS
    uf_interfaces = [
        'IAuthenticationPlugin',
        'IChallengePlugin',
        'IExtractionPlugin',
        'ICredentialsResetPlugin'
    ]

    # define which interfaces need to be moved to top of plugin list
    move_to_top_for = []

    if PLUGIN_ID not in uf.objectIds():
        manage_addOneloginSSOPlugin(uf, PLUGIN_ID, PLUGIN_TITLE)
        plugin = uf[PLUGIN_ID]
        plugin.manage_activateInterfaces(uf_interfaces)

        for interface_name in move_to_top_for:
            set_plugin_position(
                uf,
                interface_name,
                position=0
            )
        else:
            logger.warn(
                'Plugin already has been installed at {0!r}.'
                'This might be a bug? or manually installed?'.format(plugin))

    logger.info('Successfully installed plone.app.onelogin:{0}.'.format(PLUGIN_ID))


def uninstall_pas_plugin(portal):
    """ """
    logger.info('{0} plugin uninstall process is started'.format(PLUGIN_ID))

    uf = api.portal.get_tool('acl_users')

    if PLUGIN_ID in uf.objectIds():
        uf[PLUGIN_ID].manage_activateInterfaces([])
        uf.manage_delObjects([PLUGIN_ID])  # noqa: P001

    else:
        logger.warn('The plugin has already been removed! if not manually deleted, this is a bug?')

    logger.info('{0} plugin uninstall process is completed'.format(PLUGIN_ID))


def post_install(context):
    """Post install script"""
    # Do something at the end of the installation of this package.
    portal = aq_parent(context)

    # setup plugin
    install_pas_plugin(portal)

    # external login registered? @see Products.CMFPlone.skins.portal_login


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.
    portal = aq_parent(context)

    uninstall_pas_plugin(portal)
