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
        ReflogFile,
        )

from dulwich.tests import TestCase

simple_reflog = """0000000000000000000000000000000000000000 fdf4fc3344e67ab068f836878b6c4951e3b15f3d Scott Chacon <schacon@gmail.com> 1243041744 -0700\tfirst commit
fdf4fc3344e67ab068f836878b6c4951e3b15f3d cac0cab538b970a37ea1e769cbbde608743bc96d Scott Chacon <schacon@gmail.com> 1243041324 -0700\tsecond commit
cac0cab538b970a37ea1e769cbbde608743bc96d 1a410efbd13591db07496601ebc7a059dd55cfe9 Scott Chacon <schacon@gmail.com> 1243041124 -0700\tthird commit
1a410efbd13591db07496601ebc7a059dd55cfe9 484a59275031909e19aadb7c92262719cfcdf19a Scott Chacon <schacon@gmail.com> 1243041024 -0700\tadded repo.rb
484a59275031909e19aadb7c92262719cfcdf19a ab1afef80fac8e34258ff41fc1b867c702daa24b Scott Chacon <schacon@gmail.com> 1243041000 -0700\tmodified repo a bit
"""

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

    committer='Test Committer <test@nodomain.com>'
    author='Test Author <test@nodomain.com>'

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
            newsha = r.do_commit(str(i),
                                 committer=self.committer, author=self.author,
                                 commit_timestamp=i, commit_timezone=0,
                                 author_timestamp=i, author_timezone=0)
            reflog += "%s %s %s %d +%04d\t%s\n" % (oldsha, newsha,
                                                   self.committer, i, 0, i)
            self.assertEquals(r["refs/heads/master"].id, newsha)
            self._shas.append(newsha)
            oldsha = newsha

        self._reflog = reflog

    def new_reflog(self):
        rl = ReflogFile.from_file(StringIO(self._reflog))
        rl._repo = self._repo
        rl._ref = "refs/heads/master"
        return rl

    def test_getitem(self):
        rl = self.new_reflog()
        self.assertEqual({
            'old': self._shas[4],
            'new': self._shas[5],
            'user': self.committer,
            'time': 4,
            'timezone': 0,
            'timezone_neg': False,
            'msg': "4"}, rl[0])
        self.assertEqual({
            'old': self._shas[0],
            'new': self._shas[1],
            'user': self.committer,
            'time': 0,
            'timezone': 0,
            'timezone_neg': False,
            'msg': "0"}, rl[4])
        self.assertRaises(IndexError, lambda: rl[10])

    def test_get_sha_by_index(self):
        rl = self.new_reflog()
        for i in range(5+1):
            self.assertEqual(self._shas[5 - i], rl.get_sha_by_index(i))

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

            self.assertEqual({
                'old': self._shas[4 - i],
                'new': self._shas[5],
                'user': self.committer,
                'time': 4,
                'timezone': 0,
                'timezone_neg': False,
                'msg': "4"}, rl[0])

            rl.delete_entry(1, True)

        self.assertEqual({
            'old': self._shas[0],
            'new': self._shas[5],
            'user': self.committer,
            'time': 4,
            'timezone': 0,
            'timezone_neg': False,
            'msg': "4"}, rl[0])

        rl.delete_entry(0, True)
        self.assertEqual(ReflogFile(), rl)
