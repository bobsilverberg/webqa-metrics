#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import csv
import datetime
import json

import bugzilla_api


class BugzillaGatherer(object):

    def __init__(self):
        self.bmo = bugzilla_api.BugzillaAPI()
        self.bug_fields = ['assigned_to', 'component', 'creation_time', 'id',
                           'keywords', 'last_change_time', 'priority', 'product',
                           'resolution', 'severity', 'status', 'summary',
                           'whiteboard']

    def get_bugs(self):
        criteria = [{'product': 'Firefox OS',
                     'component': 'Gaia::UI Tests',
                     'component_type': 'not_equals',
                     'whiteboard': 'fromAutomation'}]
        for criteria_set in criteria:
            bug_list = self.bmo.get_bug_list(criteria_set)
            all_bugs = []
            for bug in bug_list:
                bug_obj = {}
                for field in self.bug_fields:
                    bug_obj[field] = bug[field]
                all_bugs.append(bug_obj)
            print all_bugs
        self._generate_json_file(all_bugs)
        self._generate_csv_file(all_bugs)

        return True

    def _generate_json_results(self):
        jobs = {}
        aggregated_results = {'Firefox OS': {}, 'Android': {}, 'Desktop': {}}
        final = []

        for job_name in self.config_data['marketplace_jobs']:
            jobs[job_name] = self._process_xml_results(job_name)

        for job_name in jobs:
            group = self._get_group(job_name)
            environment = self._get_environment(job_name)

            target_group = aggregated_results[group]
            for test_name in jobs[job_name]:
                test = jobs[job_name][test_name]
                if not test_name in target_group:
                    path_to_result = test['classname']
                    class_name = test['classname'].split('.')[-1]
                    path_to_result = path_to_result.replace('.%s' % class_name, '')
                    path_to_result += '/%s/%s/' % (class_name, test_name)
                    target_group[test_name] = {'test_name': test_name, 'path_to_result': path_to_result, 'passed': [], 'skipped': {}, 'failed': [], 'environments': []}
                if not environment in target_group[test_name]['environments']:
                    target_group[test_name]['environments'].append(environment)
                if test['result'] == 'passed':
                    target_group[test_name]['passed'].append(job_name)
                elif test['result'] == 'skipped':
                    if 'jobs' in target_group[test_name]['skipped']:
                        target_group[test_name]['skipped']['jobs'].append(job_name)
                    else:
                        target_group[test_name]['skipped'] = {'result': test['result'], 'detail': test['detail'], 'jobs': [job_name]}
                else:
                    target_group[test_name]['failed'].append({'result': test['result'], 'detail': test['detail'], 'jobs': [job_name]})

        for group_key in aggregated_results:
            target_group = aggregated_results[group_key]
            new_group = []
            for test_key in target_group:
                test = target_group[test_key]
                test['all_passed'] = not bool(len(test['failed']))
                new_group.append(test)
            final.append({'group': group_key, 'test_results': new_group})

        return final

    def _process_xml_results(self, job_name):
        response = requests.get(self.config_data['jenkins_artifact_url_pattern'] % job_name)
        response.raise_for_status()
        tree = et.fromstring(response.content)
        test_results = {}
        for el in tree.findall('testcase'):
            test = {'classname': el.attrib['classname']}
            if len(el.getchildren()) == 0:
                test['result'] = 'passed'
            else:
                result = el.getchildren()[0]
                test['result'] = result.tag
                test['detail'] = '%s: %s' % (result.attrib['message'], result.text)

            test_results[el.attrib['name']] = test
        return test_results

    def _get_group(self, job_name):
        if 'b2g' in job_name:
            return 'Firefox OS'
        if 'mobile' in job_name:
            return 'Android'
        return 'Desktop'

    def _get_environment(self, job_name):
        if job_name.startswith('marketplace.dev'):
            return 'dev'
        if job_name.startswith('marketplace.stage'):
            return 'stage'
        if job_name.startswith('marketplace.prod'):
            return 'prod'
        return 'unknown'

    def _generate_json_file(self, json_results):
        final = {'last_updated': str(datetime.datetime.now()), 'results': json_results}
        with open('data/bugs.json', 'w') as outfile:
            json.dump(final, outfile)

    def _generate_csv_file(self, results):
        with open('data/bugs.csv', 'w') as outfile:
            writer = csv.DictWriter(outfile, self.bug_fields)
            writer.writer.writerow(self.bug_fields)
            for dict in results:
                writer.writerow(dict)

if __name__ == '__main__':

    print 'Starting job ...'
    gatherer = BugzillaGatherer()
    print 'Job successful: %s' % gatherer.get_bugs()
