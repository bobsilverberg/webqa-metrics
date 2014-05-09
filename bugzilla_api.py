#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

import requests


class BugzillaAPI:

    def __init__(self):
        self.base_url = 'https://api-dev.bugzilla.mozilla.org/latest/'
        self.headers = {'Accept': 'application/json',
                        'Content-Type': 'application/json'}

    def _do_get(self, uri, get_params):
        """Get to an API method and return an array of objects."""
        response = requests.get("%s/%s" % (self.base_url, uri), params=get_params)
        response.raise_for_status()
        text = json.loads(response.text)
        return text

    def get_bug_list(self, criteria):

        uri = 'bug'
        bug_list = self._do_get(uri, criteria)
        return bug_list['bugs']
