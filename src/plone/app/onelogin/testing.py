# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import plone.onelogin


class PloneOneloginLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=plone.onelogin)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'plone.onelogin:default')


PLONE_ONELOGIN_FIXTURE = PloneOneloginLayer()


PLONE_ONELOGIN_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONE_ONELOGIN_FIXTURE,),
    name='PloneOneloginLayer:IntegrationTesting',
)


PLONE_ONELOGIN_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONE_ONELOGIN_FIXTURE,),
    name='PloneOneloginLayer:FunctionalTesting',
)


PLONE_ONELOGIN_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        PLONE_ONELOGIN_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='PloneOneloginLayer:AcceptanceTesting',
)
