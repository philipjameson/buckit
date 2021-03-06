# Copyright 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import absolute_import, division, print_function, unicode_literals

import tests.utils
from tests.utils import dedent


class CppBenchmarkTest(tests.utils.TestCase):
    includes = [("@fbcode_macros//build_defs:cpp_benchmark.bzl", "cpp_benchmark")]

    @tests.utils.with_project()
    def test_cpp_benchmark_parses(self, root):
        root.addFile(
            "BUCK",
            dedent(
                """
            load("@fbcode_macros//build_defs:cpp_benchmark.bzl", "cpp_benchmark")
            cpp_benchmark(
                name = "benchmark",
                srcs = [
                    "bench.cpp",
                ],
                headers = [
                    "bench.h",
                ],
                deps = [
                    ":some_dep",
                ],
            )
            cpp_benchmark(
                name = "benchmark2",
                srcs = [
                    "bench2.cpp",
                ],
                headers = {
                    "bench2.h": "subdir/bench2.h",
                },
                deps = [
                    ":some_dep",
                ],
            )
            """
            ),
        )

        self.assertSuccess(root.runAudit(["BUCK"]))
