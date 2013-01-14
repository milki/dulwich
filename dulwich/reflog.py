# reflog.py - Reference History
# Copyright (C)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your option) a later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.

"""Tracking Reference History"""

import re

from dulwich.file import GitFile
from dulwich.objects import parse_timezone, format_timezone


class ReflogList(list):

    def __init__(self, repo, ref):
        self._repo = repo

    def get_sha_by_index(self, index):
        if index == 0:
            return self[0]['new']
        else:
            return self[index - 1]['old']

    def add_entry(self, old_sha, new_sha, user, time, timezone, message):
        self.insert(0, {
            'old': old_sha,
            'new': new_sha,
            'user': user,
            'time': time,
            'timezone': timezone,
            'timezone_neg': False,
            'msg': message})

    def delete_entry(self, index, rewrite=False):
        if rewrite and index != 0:
            if index == len(self) - 1:
                self[index - 1]['old'] = self[index]['old']
            else:
                self[index - 1]['old'] = self[index + 1]['new']
        del self[index]

class ReflogFile(ReflogList):

    def _parse_file(self):
        """Parse a reflog file."""

        regex = re.compile('(?P<old>\w{40})\s(?P<new>\w{40})\s'
                           '(?P<user>.*<.*>)\s'
                           '(?P<timetext>\d+)\s'
                           '(?P<timezonetext>[-+]?\d{4})\s+'
                           '(?P<msg>.*)')

        # Start from end of file
        for lineno, line in enumerate(reversed(self._file.readlines())):
            line = line.strip()
            match = regex.match(line)

            if match is None:
                # Corrupt reflog, stop parsing
                return

            matchd = match.groupdict()
            matchd['time'] = int(matchd['timetext'])
            matchd['timezone'], matchd['timezone_neg'] = \
                parse_timezone(matchd['timezonetext'])
            del matchd['timetext']
            del matchd['timezonetext']

            self.append(matchd)

    @classmethod
    def from_path(cls, path):
        f = GitFile(path, 'rb')
        try:
            obj = cls.from_file(f)
            obj._path = path
            return obj
        finally:
            f.close()

    @classmethod
    def from_file(cls, f):
        ret = cls()
        ret._file = f
        ret._parse_file()
        return ret

    def write_to_path(self, path=None):
        if path is None:
            path = self.path
        f = GitFile(path, 'wb')
        try:
            self.write_to_file(f)
        finally:
            f.close()

    def write_to_file(self, f):
        for log in reversed(self):
            f.write("%s %s %s %s %s\t%s\n" % (log['old'],
                                              log['new'],
                                              log['user'],
                                              log['time'],
                                              format_timezone(
                                                  log['timezone'],
                                                  log['timezone_neg']),
                                              log['msg']))
