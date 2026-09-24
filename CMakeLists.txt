cmake_minimum_required(VERSION 3.18)
project(pysciencemode LANGUAGES C)

# Builds the `sciencemode._sciencemode` cffi extension (API mode) on top of a
# static build of HASOMED's ScienceMode4 C library (git submodule).
# Driven by scikit-build-core (see pyproject.toml); `pip install .` is enough.

set(SMPT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/extern/ScienceMode4_c_library")
set(SMPT_LIB "${SMPT_ROOT}/ScienceMode_Library")
if(NOT EXISTS "${SMPT_LIB}/src/general/smpt_client.c")
  message(FATAL_ERROR
    "ScienceMode4 C library sources not found in ${SMPT_ROOT}.\n"
    "Run: git submodule update --init --recursive")
endif()

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

# --- Static ScienceMode4 library (general + low-level + mid-level) ----------
# We define our own target instead of add_subdirectory() so that the upstream
# test executable and install() rules do not end up in the wheel. The dyscom
# level is not built: its client API is disabled upstream on macOS and it is
# not used by pysciencemode.
file(GLOB SMPT_SOURCES CONFIGURE_DEPENDS
  "${SMPT_LIB}/src/general/*.c"
  "${SMPT_LIB}/src/general/packet/*.c"
  "${SMPT_LIB}/src/general/packet_input_buffer/*.c"
  "${SMPT_LIB}/src/general/packet_output_buffer/*.c"
  # Each OS-specific file is fully guarded by #ifdef _WIN32 / __linux__ /
  # __APPLE__, so compiling all of them is correct on every platform.
  "${SMPT_LIB}/src/general/serial_port/*.c"
  "${SMPT_LIB}/src/low-level/*.c"
  "${SMPT_LIB}/src/mid-level/*.c"
)
add_library(smpt STATIC ${SMPT_SOURCES})
set_target_properties(smpt PROPERTIES
  C_STANDARD 99
  POSITION_INDEPENDENT_CODE ON)
target_include_directories(smpt PUBLIC
  "${SMPT_LIB}/include"
  "${SMPT_LIB}/include/general"
  "${SMPT_LIB}/include/general/packet"
  "${SMPT_LIB}/include/general/packet_input_buffer"
  "${SMPT_LIB}/include/general/packet_output_buffer"
  "${SMPT_LIB}/include/general/serial_port"
  "${SMPT_LIB}/include/low-level"
  "${SMPT_LIB}/include/mid-level")
target_compile_definitions(smpt PUBLIC SMPT_LOW_LEVEL SMPT_MID_LEVEL)
if(MSVC)
  target_compile_definitions(smpt PUBLIC _CRT_SECURE_NO_WARNINGS)
endif()
if(UNIX)
  target_link_libraries(smpt PUBLIC m)
endif()

# --- cffi extension ---------------------------------------------------------
set(FFI_BUILDER "${CMAKE_CURRENT_SOURCE_DIR}/tools/cffi/build_ffi.py")
set(FFI_CDEF "${CMAKE_CURRENT_SOURCE_DIR}/tools/cffi/smpt_cdef.h")
set(FFI_C "${CMAKE_CURRENT_BINARY_DIR}/_sciencemode.c")
add_custom_command(
  OUTPUT "${FFI_C}"
  COMMAND "${Python_EXECUTABLE}" "${FFI_BUILDER}" "${FFI_C}"
  DEPENDS "${FFI_BUILDER}" "${FFI_CDEF}"
  COMMENT "Generating cffi C source for sciencemode._sciencemode"
  VERBATIM)

python_add_library(_sciencemode MODULE WITH_SOABI "${FFI_C}")
target_link_libraries(_sciencemode PRIVATE smpt)

install(TARGETS _sciencemode LIBRARY DESTINATION sciencemode)
# The bundled C library is MPL-2.0 OR LGPL-3.0-or-later: ship its licenses
# next to the compiled code.
install(FILES "${SMPT_ROOT}/LICENSE" DESTINATION sciencemode RENAME LICENSE.ScienceMode4.MPL-2.0)
install(FILES "${SMPT_ROOT}/LICENSE_LGPL_3_0" DESTINATION sciencemode RENAME LICENSE.ScienceMode4.LGPL-3.0)
