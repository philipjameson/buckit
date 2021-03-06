# Copyright 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import absolute_import, division, print_function, unicode_literals

import tests.utils
from tests.utils import dedent


class DUnitTestTest(tests.utils.TestCase):
    includes = [("@fbcode_macros//build_defs:d_unittest.bzl", "d_unittest")]

    @tests.utils.with_project()
    def test_d_unittest_parses(self, root):
        root.addFile(
            "BUCK",
            dedent(
                """
            load("@fbcode_macros//build_defs:d_unittest.bzl", "d_unittest")
            d_unittest(
                name = "MainBin",
                srcs = [
                    "MainBin.d",
                ],
                linker_flags = [
                    "--script=$(location :linker_script)",
                ],
                deps = [
                    "//folly:singleton",
                ],
                tags = ["some_tag"],
            )

            """
            ),
        )

        self.assertSuccess(root.runAudit(["BUCK"]))
