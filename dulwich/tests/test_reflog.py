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
