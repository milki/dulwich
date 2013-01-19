# test_reflog.py -- Tests for reading and writing reflogs
# Copyright (C)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# or (at your option) a later version of the License.
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

"""Tests for reading and writing reflogs."""

from cStringIO import StringIO
import shutil
import tempfile
import os

from dulwich.repo import (
    Repo,
)
from dulwich.reflog import (
    Reflog,
    ReflogFile,
)
from dulwich.errors import (
    RefFormatError,
)

from dulwich.tests import TestCase

simple_reflog = """0000000000000000000000000000000000000000 fdf4fc3344e67ab068f836878b6c4951e3b15f3d Scott Chacon <schacon@gmail.com> 1243041744 -0700\tfirst commit
fdf4fc3344e67ab068f836878b6c4951e3b15f3d cac0cab538b970a37ea1e769cbbde608743bc96d Scott Chacon <schacon@gmail.com> 1243041324 -0700\tsecond commit
cac0cab538b970a37ea1e769cbbde608743bc96d 1a410efbd13591db07496601ebc7a059dd55cfe9 Scott Chacon <schacon@gmail.com> 1243041124 -0700\tthird commit
1a410efbd13591db07496601ebc7a059dd55cfe9 484a59275031909e19aadb7c92262719cfcdf19a Scott Chacon <schacon@gmail.com> 1243041024 -0700\tadded repo.rb
484a59275031909e19aadb7c92262719cfcdf19a ab1afef80fac8e34258ff41fc1b867c702daa24b Scott Chacon <schacon@gmail.com> 1243041000 -0700\tmodified repo a bit
"""

committer = 'Test Committer <test@nodomain.com>'
author = 'Test Author <test@nodomain.com>'


class ReflogFileTests(TestCase):

    def from_file(self, text):
        return ReflogFile.from_file(StringIO(text))

    def test_empty(self):
        ReflogFile()

    def test_from_file_empty(self):
        rl = self.from_file("")
        self.assertEqual(ReflogFile(), rl)

    def test_write_to_file_empty(self):
        rl = ReflogFile()
        f = StringIO()
        rl.write_to_file(f)
        self.assertEqual("", f.getvalue())

    def test_from_file(self):
        rl = self.from_file(simple_reflog)
        f = StringIO()
        rl.write_to_file(f)
        self.assertEqual(simple_reflog, f.getvalue())


class ReflogListTests(TestCase):

    def setUp(self):
        super(ReflogListTests, self).setUp()

        repo_dir = os.path.join(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, repo_dir)
        r = self._repo = Repo.init(repo_dir)

        self._shas = []
        reflog = ""

        oldsha = "0" * 40

        self._shas = [oldsha]
        for i in range(5):
            newsha = self._make_commit(i)
            reflog += "%s %s %s %d +%04d\t%s\n" % (oldsha, newsha,
                                                   committer, i, 0, i)
            self.assertEquals(r["refs/heads/master"].id, newsha)
            self._shas.append(newsha)
            oldsha = newsha

        self._reflog = reflog

    def _make_commit(self, i):
        return self._repo.do_commit(
            str(i),
            committer=committer, author=author,
            commit_timestamp=i, commit_timezone=0,
            author_timestamp=i, author_timezone=0)

    def assertLogEntry(self, expected, entry):
        meta = {'user': committer,
                'timezone': 0,
                'timezone_neg': False,
                }
        expected.update(meta)
        self.assertEquals(expected, entry)

    def new_reflog(self):
        rl = ReflogFile.from_file(StringIO(self._reflog))
        rl._repo = self._repo
        rl._ref = "refs/heads/master"
        return rl

    def test_getitem(self):
        rl = self.new_reflog()
        for i in range(5):
            self.assertLogEntry(
                {'old': self._shas[i], 'new': self._shas[i + 1],
                 'time': i, 'msg': str(i)},
                rl[4 - i])
        self.assertRaises(IndexError, lambda: rl[10])

    def test_get_sha_by_index(self):
        rl = self.new_reflog()
        for i in range(5+1):
            self.assertEqual(self._shas[5 - i], rl.get_sha_by_index(i))

    def test_shas(self):
        rl = self.new_reflog()
        self.assertEqual(self._shas, list(reversed(rl.shas())))

    def test_add_entry(self):
        rl = ReflogFile()

        rl.add_entry('0000000000000000000000000000000000000000',
                     'fdf4fc3344e67ab068f836878b6c4951e3b15f3d',
                     'Scott Chacon <schacon@gmail.com>',
                     1243041744,
                     -60 * 60 * 7,
                     'first commit')
        line = simple_reflog.split("\n")[0] + "\n"

        f = StringIO()
        rl.write_to_file(f)
        self.assertEqual(line, f.getvalue())

    def test_delete_entry(self):
        rl = self.new_reflog()

        for i in range(5):
            rl.delete_entry(0)
        self.assertEqual(ReflogFile(), rl)

        rl = self.new_reflog()
        for i in range(4):
            self.assertLogEntry(
                {'old': self._shas[4 - i], 'new': self._shas[5],
                 'time': 4, 'msg': "4"},
                rl[0])

            rl.delete_entry(1, True)
        self.assertLogEntry(
            {'old': self._shas[0], 'new': self._shas[5],
             'time': 4, 'msg': "4"},
            rl[0])

        rl.delete_entry(0, True)
        self.assertEqual(ReflogFile(), rl)


class ReflogTests(TestCase):

    def setUp(self):
        super(ReflogTests, self).setUp()

        repo_dir = os.path.join(tempfile.mkdtemp())
        r = self._repo = Repo.init(repo_dir)

        self._shas = []
        reflog = ""

        self._oldsha = "0" * 40
        self._newsha = r.do_commit(
            "0", committer=committer, author=author,
            commit_timestamp=0, commit_timezone=0,
            author_timestamp=0, author_timezone=0)

        rl = ReflogFile()
        rl.add_entry(self._oldsha, self._newsha,
                     committer, 0, 0, "0")
        self._reflog = Reflog(r)
        self._reflog._reflogs = {"refs/heads/master": rl}

    def _make_commit(self, i):
        rl = self._reflog

        oldsha = rl.get_sha_by_index("refs/heads/master", 0)
        newsha = self._repo.do_commit(
            str(i), committer=committer, author=author,
            commit_timestamp=i, commit_timezone=0,
            author_timestamp=i, author_timezone=0)
        rl.add_entry("refs/heads/master", oldsha, newsha,
                     committer, i + 1, 0, i + 1)
        return newsha

    def assertLogEntry(self, expected, entry):
        meta = {'user': committer,
                'timezone': 0,
                'timezone_neg': False,
                }
        expected.update(meta)
        self.assertEquals(expected, entry)

    def test_get_sha_by_index(self):
        rl = self._reflog

        self.assertEquals(self._newsha,
                          rl.get_sha_by_index("refs/heads/master", 0))
        self.assertEquals(self._oldsha,
                          rl.get_sha_by_index("refs/heads/master", 1))
        self.assertRaises(
            RefFormatError,
            lambda: rl.get_sha_by_index("ENOENT", 0))

    def test_walk(self):
        r = self._repo
        rl = self._reflog

        shas = [rl.get_sha_by_index("refs/heads/master", 0)]
        for i in range(4):
            shas.append(self._make_commit(i+1))
        self.assertEquals(5, len(rl._reflogs["refs/heads/master"]))

        self.assertEquals(
            list(reversed(shas)),
            [entry.commit.id for entry in rl.walk("refs/heads/master")])

    def test_log_by_index(self):
        rl = self._reflog

        self.assertEqual({
            'old': self._oldsha,
            'new': self._newsha,
            'user': committer,
            'time': 0,
            'timezone': 0,
            'timezone_neg': False,
            'msg': "0"}, rl.get_log_by_index("refs/heads/master", 0))

    def test_add_entry(self):
        r = self._repo
        rl = self._reflog

        commit = self._make_commit(1)

        self.assertEquals(commit,
                          rl.get_sha_by_index("refs/heads/master", 0))
        self.assertEquals(self._newsha,
                          rl.get_sha_by_index("refs/heads/master", 1))
        self.assertEquals(self._oldsha,
                          rl.get_sha_by_index("refs/heads/master", 2))

    def test_delete_entry(self):
        r = self._repo
        rl = self._reflog

        shas = [self._oldsha, rl.get_sha_by_index("refs/heads/master", 0)]
        for i in range(4):
            commit = self._make_commit(i+2)
            shas.append(commit)
        self.assertEquals(5, len(rl._reflogs["refs/heads/master"]))

        # 5 commits, 6 shas, 5 log entries
        for i in range(5):
            rl.delete_entry("refs/heads/master", 0)

        self.assertEquals(0, len(rl._reflogs["refs/heads/master"]))
        self.assertEquals(shas[5], rl.get_sha_by_index("refs/heads/master", 0))
        self.assertRaises(
            IndexError,
            lambda: rl.get_sha_by_index("refs/heads/master", 1))

        rl.add_entry("refs/heads/master", self._oldsha, self._newsha,
                     committer, 0, 0, "1")
        for i in range(4):
            rl.add_entry("refs/heads/master", shas[i + 1], shas[i + 2],
                         committer, i + 1, 0, i + 1)
        self.assertEquals(5, len(rl._reflogs["refs/heads/master"]))

        for i in range(4):
            self.assertLogEntry(
                {'old': shas[4 - i], 'new': shas[5],
                 'time': 4, 'msg': "4"},
                rl.get_log_by_index("refs/heads/master", 0))

            rl.delete_entry("refs/heads/master", 1, True)
        self.assertEquals(1, len(rl._reflogs["refs/heads/master"]))

        rl.delete_entry("refs/heads/master", 0, True)
        self.assertRaises(
            IndexError,
            lambda: rl.get_log_by_index("refs/heads/master", 0))
