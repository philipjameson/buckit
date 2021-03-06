# Copyright 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import absolute_import, division, print_function, unicode_literals

import tests.utils
from tests.utils import dedent


class CppPythonExtensionTest(tests.utils.TestCase):
    includes = [
        ("@fbcode_macros//build_defs:cpp_python_extension.bzl", "cpp_python_extension")
    ]

    @tests.utils.with_project()
    def test_cpp_python_extension_parses(self, root):
        root.addFile(
            "BUCK",
            dedent(
                """
            load("@fbcode_macros//build_defs:cpp_python_extension.bzl", "cpp_python_extension")
            cpp_python_extension(
                name = "Files",
                headers = ["Files.h"],
                srcs = ["Files.cpp"],
                base_module = "storage.fs",
                deps = [
                    ":file_api",
                ],
                external_deps = [
                    ("boost", None, "boost_python"),
                ],
            )
            """
            ),
        )

        self.assertSuccess(root.runAudit(["BUCK"]))
