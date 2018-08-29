#!/usr/bin/env python3
'''
This test shows off the full power of the `btrfs_diff` toolkit.

 (1) Start out with the binary send-streams generated by
     `demo_sendstreams.py`, which represent subvolumes exercising all the
     core functions of btrfs.
 (2) Parse & receive the send-streams into an in-memory filesystem.
 (3) Ensure the subvolumes looks completely specified.
 (4) Prune the "boring" metadata that is the same almost always.
 (5) Render the subvolumes and compare them to "gold" rendering, which
     was manually composed from the script in `demo_sendstreams.py`.

This demonstrates that we have an essentially complete mock of btrfs, with
the ability to easily express complex assertions about send-streams and
filesystems.

In effect, we jointly test the Linux kernel, btrfs-progs, and this library.
'''
import io
import os
import unittest

from ..freeze import freeze
from ..rendered_tree import emit_non_unique_traversal_ids
from ..subvolume_set import SubvolumeSet

from . import render_subvols as render_sv

from .demo_sendstreams import gold_demo_sendstreams
from .demo_sendstreams_expected import render_demo_subvols


class SendstreamToSubvolumeSetIntegrationTestCase(unittest.TestCase):

    def setUp(self):  # More output for easier debugging
        unittest.util._MAX_LENGTH = 12345
        self.maxDiff = 12345

    def test_integration(self):
        # Convert the known-good, version-control-recorded copies of the
        # demo sendstreams into a `SubvolumeSet`.
        stream_dict = gold_demo_sendstreams()
        subvols = SubvolumeSet.new()
        for d in stream_dict.values():
            render_sv.add_sendstream_to_subvol_set(subvols, d['sendstream'])
        render_sv.prepare_subvol_set_for_render(
            subvols,
            build_start_time=stream_dict['create_ops']['build_start_time'],
            build_end_time=stream_dict['mutate_ops']['build_end_time'],
        )

        # Rendering the subvolumes individually shows fewer clones than
        # rendering them together.
        self.assertEqual(
            render_demo_subvols(create_ops=True),
            render_sv.render_subvolume(
                subvols.get_by_rendered_id('create_ops'),
            ),
        )
        self.assertEqual(
            render_demo_subvols(mutate_ops=True),
            render_sv.render_subvolume(
                subvols.get_by_rendered_id('mutate_ops'),
            ),
        )
        self.assertEqual(
            render_demo_subvols(create_ops=True, mutate_ops=True),
            freeze(subvols).map(
                lambda sv: emit_non_unique_traversal_ids(sv.render())
            ),
        )


if __name__ == '__main__':
    unittest.main()
