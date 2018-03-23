# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.onelogin.testing import PLONE_ONELOGIN_INTEGRATION_TESTING  # noqa

import unittest


class TestSetup(unittest.TestCase):
    """Test that plone.onelogin is properly installed."""

    layer = PLONE_ONELOGIN_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if plone.onelogin is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'plone.onelogin'))

    def test_browserlayer(self):
        """Test that IPloneOneloginLayer is registered."""
        from plone.onelogin.interfaces import (
            IPloneOneloginLayer)
        from plone.browserlayer import utils
        self.assertIn(
            IPloneOneloginLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = PLONE_ONELOGIN_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['plone.onelogin'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if plone.onelogin is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'plone.onelogin'))

    def test_browserlayer_removed(self):
        """Test that IPloneOneloginLayer is removed."""
        from plone.onelogin.interfaces import \
            IPloneOneloginLayer
        from plone.browserlayer import utils
        self.assertNotIn(
           IPloneOneloginLayer,
           utils.registered_layers())
