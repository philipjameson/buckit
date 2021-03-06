#!/usr/bin/env python3
import contextlib
import os
import tempfile

from typing import AnyStr

from artifacts_dir import ensure_per_repo_artifacts_dir_exists
from subvol_utils import byteme, Subvol
from volume_for_repo import get_volume_for_current_repo


class TempSubvolumes(contextlib.AbstractContextManager):
    '''
    Tracks the subvolumes it creates, and destroys them on context exit.

    Note that relying on unittest.TestCase.addCleanup to __exit__ this
    context is unreliable -- e.g. clean-up is NOT triggered on
    KeyboardInterrupt. Therefore, this **will** leak subvolumes
    during development. You can clean them up thus:

        sudo btrfs sub del buck-image-out/volume/tmp/TempSubvolumes_*/subvol &&
            rmdir buck-image-out/volume/tmp/TempSubvolumes_*

    Instead of polluting `buck-image-out/volume`, it  would be possible to
    put these on a separate `LoopbackVolume`, to rely on `Unshare` to
    guarantee unmounting it, and to rely on `tmpwatch` to delete the stale
    loopbacks from `/tmp/`.  At present, this doesn't seem worthwhile since
    it would require using an `Unshare` object throughout `Subvol`.

    The easier approach is to write `with TempSubvolumes() ...` in each test.
    '''

    def __init__(self, path_in_repo):
        self.subvols = []
        # The 'tmp' subdirectory simplifies cleanup of leaked temp subvolumes
        volume_tmp_dir = os.path.join(get_volume_for_current_repo(
            1e8, ensure_per_repo_artifacts_dir_exists(path_in_repo),
        ), 'tmp')
        try:
            os.mkdir(volume_tmp_dir)
        except FileExistsError:
            pass
        # Our exit is written with exception-safety in mind, so this
        # `_temp_dir_ctx` **should** get `__exit__`ed when this class does.
        self._temp_dir_ctx = tempfile.TemporaryDirectory(  # noqa: P201
            dir=volume_tmp_dir,
            prefix=self.__class__.__name__ + '_',
        )

    def __enter__(self):
        self._temp_dir = self._temp_dir_ctx.__enter__().encode()
        return self

    def _rel_path(self, rel_path: AnyStr):
        '''
        Ensures subvolumes live under our temporary directory, which
        improves safety, since its permissions ought to be u+rwx to avoid
        exposing setuid binaries inside the built subvolumes.
        '''
        rel_path = os.path.relpath(
            os.path.realpath(
                os.path.join(self._temp_dir, byteme(rel_path)),
            ),
            start=os.path.realpath(self._temp_dir),
        )
        if (
            rel_path == b'..' or rel_path.startswith(b'../') or
            os.path.isabs(rel_path)
        ):
            raise AssertionError(
                f'{rel_path} must be a subdirectory of {self._temp_dir}'
            )
        return os.path.join(self._temp_dir, rel_path)

    def create(self, rel_path: AnyStr) -> Subvol:
        subvol = Subvol(self._rel_path(rel_path))
        subvol.create()
        self.subvols.append(subvol)
        return subvol

    def snapshot(self, source: Subvol, dest_rel_path: AnyStr) -> Subvol:
        dest = Subvol(self._rel_path(dest_rel_path))
        dest.snapshot(source)
        self.subvols.append(dest)
        return dest

    def caller_will_create(self, rel_path: AnyStr) -> Subvol:
        subvol = Subvol(self._rel_path(rel_path))
        # If the caller fails to create it, our __exit__ is robust enough
        # to ignore this subvolume.
        self.subvols.append(subvol)
        return subvol

    def __exit__(self, exc_type, exc_val, exc_tb):
        # If any of subvolumes are nested, and the parents were made
        # read-only, we won't be able to delete them.
        for subvol in self.subvols:
            try:
                subvol.set_readonly(False)
            except BaseException:  # Ctrl-C does not interrupt cleanup
                pass
        for subvol in reversed(self.subvols):
            try:
                subvol.delete()
            except BaseException:  # Ctrl-C does not interrupt cleanup
                pass
        return self._temp_dir_ctx.__exit__(exc_type, exc_val, exc_tb)
