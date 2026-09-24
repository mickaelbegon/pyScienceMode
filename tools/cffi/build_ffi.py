"""Emit the C source of the ``sciencemode._sciencemode`` cffi extension (API mode).

Called by CMake at build time (see the top-level CMakeLists.txt)::

    python tools/cffi/build_ffi.py <output.c>

It only needs the ``cffi`` package (and its pure-Python ``pycparser``
dependency, used to parse the committed ``smpt_cdef.h``). The generated C file
is compiled and linked against the static ``smpt`` library by CMake, which
provides the include directories and the ``SMPT_LOW_LEVEL`` /
``SMPT_MID_LEVEL`` definitions.
"""

import sys
from pathlib import Path

from cffi import FFI

HERE = Path(__file__).resolve().parent

SOURCE = """
#include "smpt_definitions.h"
#include "smpt_client.h"
#include "smpt_client_utils.h"
#include "smpt_client_power.h"
#include "smpt_packet_number_generator.h"
#include "smpt_ll_definitions.h"
#include "smpt_ll_client.h"
#include "smpt_ml_definitions.h"
#include "smpt_ml_client.h"
"""


def make_ffi() -> FFI:
    ffi = FFI()
    ffi.cdef((HERE / "smpt_cdef.h").read_text(encoding="utf-8"))
    ffi.set_source("sciencemode._sciencemode", SOURCE)
    return ffi


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} <output.c>")
    out = Path(sys.argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    make_ffi().emit_c_code(str(out))


if __name__ == "__main__":
    main()
