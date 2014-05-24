#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import csv
import datetime
import json

from matplotlib.dates import date2num
import matplotlib.pyplot as plt
import numpy as np
import bugzilla_api


class BugzillaGatherer(object):

    def __init__(self):
        self.bmo = bugzilla_api.BugzillaAPI()
        self.bug_fields = ['assigned_to', 'component', 'creation_time', 'creator',
                           'id', 'keywords', 'last_change_time', 'priority', 'product',
                           'qa_contact', 'resolution', 'severity', 'status', 'summary',
                           'whiteboard']

    def compare_fromAutomation_vs_not_over_time(self, product, created_after):
        criteria = {'product': product,
                     'resolution': 'INVALID',
                     'resolution': 'WONTFIX',
                     'resolution': 'WORKSFORME',
                     'resolution': 'INCOMPLETE',
                     'resolution_type': 'not_equals',
                     'whiteboard': 'fromAutomation',
                     'changed_after': created_after,
                     'changed_field': 'creation_time'}
        bug_list_yes = self.bmo.get_bug_list(criteria)
        criteria['keywords'] = 'regression'
        criteria['whiteboard_type'] = 'not_contains'
        bug_list_no_reg = self.bmo.get_bug_list(criteria)
        criteria['keywords_type'] = 'not_contains'
        bug_list_no__not_reg = self.bmo.get_bug_list(criteria)
        count_by_date_yes = {}
        count_by_date_no_reg = {}
        count_by_date_no_not_reg = {}
        for bug in bug_list_yes:
            the_date = datetime.datetime.strptime(bug['last_change_time'][0:7], "%Y-%m")
            if the_date not in count_by_date_yes:
                count_by_date_yes[the_date] = 0
            count_by_date_yes[the_date] += 1
        print len(count_by_date_yes)
        print count_by_date_yes
        print sorted(count_by_date_yes)
        for bug in bug_list_no_reg:
            the_date = datetime.datetime.strptime(bug['last_change_time'][0:7], "%Y-%m")
            # the_date = datetime.datetime.strptime(bug['last_change_time'], "%Y-%m-%dT%H:%M:%SZ").date()
            if the_date not in count_by_date_no_reg:
                count_by_date_no_reg[the_date] = 0
            count_by_date_no_reg[the_date] += 1
        print len(count_by_date_no_reg)
        print count_by_date_no_reg
        print sorted(count_by_date_no_reg)
        for bug in bug_list_no__not_reg:
            the_date = datetime.datetime.strptime(bug['last_change_time'][0:7], "%Y-%m")
            # the_date = datetime.datetime.strptime(bug['last_change_time'], "%Y-%m-%dT%H:%M:%SZ").date()
            if the_date not in count_by_date_no_not_reg:
                count_by_date_no_not_reg[the_date] = 0
            count_by_date_no_not_reg[the_date] += 1
        print len(count_by_date_no_not_reg)
        print count_by_date_no_not_reg
        print sorted(count_by_date_no_not_reg)

        # min_date = date2num(min(count_by_date_no.keys()))
        # max_date = date2num(max(count_by_date_no.keys()))
        # days = max_date - min_date + 1

        # Initialize X and Y axes
        months = len(count_by_date_no_not_reg)
        x = np.arange(1, len(count_by_date_no_not_reg) + 1)
        y_yes = np.zeros(months)
        y_no_reg = np.zeros(months)
        y_no_not_reg = np.zeros(months)

        print x

        index = 0
        for date in sorted(count_by_date_no_not_reg):
            y_no_not_reg[index] = count_by_date_no_not_reg[date] / 10
            if date in count_by_date_yes:
                y_yes[index] = count_by_date_yes[date]
            if date in count_by_date_no_reg:
                y_no_reg[index] = count_by_date_no_reg[date]
            index += 1
        print y_yes
        print y_no_reg
        print y_no_not_reg

        # Plot line graph
        fig, ax = plt.subplots()
        yes_set = ax.plot(x, y_yes, color='g')
        no_reg_set = ax.plot(x, y_no_reg, color='r')
        no_not_reg_set = ax.plot(x, y_no_not_reg, color='y')

        # add some
        ax.set_ylabel('Bugs Filed')
        ax.set_title('Bugs Filed for %s by fromAutomation and not' % product)
        ax.set_xticks(x)
        ax.set_xticklabels([date.strftime('%Y-%m') for date in sorted(count_by_date_no_not_reg)], rotation='vertical')

        fig.set_size_inches(18.5,10.5)
        plt.savefig('%s-both-fromAutomation-plot-div-by-10.png' % product)

        # Plot bar graph
        width = .5       # the width of the bars
        fig, ax = plt.subplots()
        yes_set = ax.bar(x, y_yes, width, color='g')
        no_set = ax.bar(x+width/2, y_no_reg, width, color='r')
        no__not_reg_set = ax.bar(x+width, y_no_not_reg, width, color='y')

        # add some
        ax.set_ylabel('Bugs Filed')
        ax.set_title('Bugs Filed for %s by fromAutomation and not' % product)
        ax.set_xticks(x+width)
        ax.set_xticklabels([date.strftime('%Y-%m') for date in sorted(count_by_date_no_not_reg)], rotation='vertical')

        # plt.plot_date(x, y, xdate=True, ydate=False, ls='-', ms=0, color='#16171E')
        fig.set_size_inches(18.5,10.5)
        plt.savefig('%s-both-fromAutomation-bar-div-by-10.png' % product)
        # pyplot.show()

        print 'All doooone!'


    def get_bugs(self):
        criteria = [{'whiteboard': 'fromAutomation'}]
        bugs_per_product_component = {}
        bugs_per_creator = {}
        all_creators = []
        for criteria_set in criteria:
            bug_list = self.bmo.get_bug_list(criteria_set)
            all_bugs = []
            for bug in bug_list:
                pc_key = '%s - %s' % (bug['product'], bug['component'])
                creator = '%s - %s' % (bug['creator']['name'], bug['creator'].get('real_name', ''))
                if bug['creator']['name'] not in all_creators:
                    all_creators.append(bug['creator']['name'])
                if pc_key not in bugs_per_product_component:
                    bugs_per_product_component[pc_key] = 0
                if creator not in bugs_per_creator:
                    bugs_per_creator[creator] = 0
                bugs_per_product_component[pc_key] += 1
                bugs_per_creator[creator] += 1
                bug_obj = {}
                for field in self.bug_fields:
                    value = bug[field]
                    if type(value) is dict:
                        bug_obj[field] = value.values()
                    else:
                        bug_obj[field] = value
                all_bugs.append(bug_obj)
        #     print all_bugs
        # self._generate_json_file(all_bugs)
        # self._generate_csv_file(all_bugs, self.bug_fields)
        # bugs_per_product_component_list = []
        # bugs_per_creator_list = []
        # for key, value in bugs_per_product_component.iteritems():
        #     temp = {'product_component': key, 'bug_count': str(value)}
        #     bugs_per_product_component_list.append(temp)
        # self._generate_csv_file(bugs_per_product_component_list, ['product_component', 'bug_count'], 'bugs_per_product_component')
        # for key, value in bugs_per_creator.iteritems():
        #     temp = {'creator': key, 'bug_count': str(value)}
        #     bugs_per_creator_list.append(temp)
        # self._generate_csv_file(bugs_per_creator_list, ['creator', 'bug_count'], 'bugs_per_creator')

        # get bugs for each user who used fromAutomation
        all_bugs = []
        for creator in all_creators:
            print 'Getting bugs for %s...' % creator
            criteria = {'email1': creator, 'emailreporter1': 1, 'emailtype1': 'substring'}
            bug_list = self.bmo.get_bug_list(criteria)
            for bug in bug_list:
                bug_obj = {}
                for field in self.bug_fields:
                    value = bug[field]
                    if type(value) is dict:
                        bug_obj[field] = value.values()
                    else:
                        bug_obj[field] = value
                all_bugs.append(bug_obj)
        print all_bugs
        self._generate_csv_file(all_bugs, self.bug_fields, 'all_bugs_by_everyone')

        return True

    def _generate_json_file(self, json_results):
        final = {'last_updated': str(datetime.datetime.now()), 'results': json_results}
        with open('data/bugs.json', 'w') as outfile:
            json.dump(final, outfile)

    def _generate_csv_file(self, results, fields, name='bugs'):
        with open('data/%s.csv' % name, 'w') as outfile:
            writer = csv.DictWriter(outfile, fields)
            writer.writer.writerow(self.bug_fields)
            for dict in results:
                try:
                    writer.writerow(dict)
                except:
                    pass

if __name__ == '__main__':

    print 'Starting job ...'
    gatherer = BugzillaGatherer()
    print 'Job successful: %s' % gatherer.compare_fromAutomation_vs_not_over_time('addons.mozilla.org', '2010-05-01')
