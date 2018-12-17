#!/usr/bin/env python2

# Copyright 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections
import itertools
import pipes

# Hack to make internal Buck macros flake8-clean until we switch to buildozer.
def import_macro_lib(path):
    global _import_macro_lib__imported
    include_defs('{}/{}.py'.format(  # noqa: F821
        read_config('fbcode', 'macro_lib', '//macro_lib'), path  # noqa: F821
    ), '_import_macro_lib__imported')
    ret = _import_macro_lib__imported
    del _import_macro_lib__imported  # Keep the global namespace clean
    return ret


base = import_macro_lib('convert/base')
Rule = import_macro_lib('rule').Rule
target = import_macro_lib('fbcode_target')
load("@bazel_skylib//lib:paths.bzl", "paths")
load("@bazel_skylib//lib:shell.bzl", "shell")
load("@bazel_skylib//lib:new_sets.bzl", "sets")
load("@fbcode_macros//build_defs/lib:python_typing.bzl",
     "get_typing_config_target")
load("@fbcode_macros//build_defs:cpp_library.bzl", "cpp_library")
load("@fbcode_macros//build_defs:custom_rule.bzl", "get_project_root_from_gen_dir")
load("@fbcode_macros//build_defs:java_library.bzl", "java_library")
load("@fbcode_macros//build_defs:cython_library.bzl", "cython_library")
load("@fbcode_macros//build_defs/lib:merge_tree.bzl", "merge_tree")
load("@fbcode_macros//build_defs:platform_utils.bzl", "platform_utils")
load("@fbcode_macros//build_defs/lib:target_utils.bzl", "target_utils")
load("@fbcode_macros//build_defs/lib:src_and_dep_helpers.bzl", "src_and_dep_helpers")
load("@fbcode_macros//build_defs/lib:haskell_common.bzl", "haskell_common")
load("@fbcode_macros//build_defs/lib:haskell_rules.bzl", "haskell_rules")
load("@fbcode_macros//build_defs/lib:third_party.bzl", "third_party")
load("@fbcode_macros//build_defs/lib:python_typing.bzl", "gen_typing_config")
load("@fbcode_macros//build_defs:config.bzl", "config")
load("@fbcode_macros//build_defs/lib:visibility.bzl", "get_visibility")
load("@fbsource//tools/build_defs:fb_native_wrapper.bzl", "fb_native")
load("@fbsource//tools/build_defs:buckconfig.bzl", "read_bool", "read_list")
load("@fbcode_macros//build_defs/lib:thrift_common.bzl", "thrift_common")
load("@fbcode_macros//build_defs/lib/thrift:thrift_interface.bzl", "thrift_interface")
load("@fbcode_macros//build_defs/lib/thrift:d.bzl", "d_thrift_converter")
load("@fbcode_macros//build_defs/lib/thrift:rust.bzl", "rust_thrift_converter")
load("@fbcode_macros//build_defs/lib/thrift:python3.bzl", "python3_thrift_converter")
load("@fbcode_macros//build_defs/lib/thrift:thriftdoc_python.bzl", "thriftdoc_python_thrift_converter")
load("@fbcode_macros//build_defs/lib/thrift:go.bzl", "go_thrift_converter")
load("@fbcode_macros//build_defs:thrift_library.bzl", "py_remote_binaries")
load("@fbcode_macros//build_defs/lib:common_paths.bzl", "common_paths")




# The capitalize method from the string will also make the
# other characters in the word lower case.  This version only
# makes the first character upper case.
def capitalize(word):
    if len(word) > 0:
        return word[0].upper() + word[1:]
    return word


def camel(s):
    return ''.join(w[0].upper() + w[1:] for w in s.split('_') if w != '')




class ThriftLangConverter(base.Converter):
    """
    Base class for language-specific converters.  New languages should
    subclass this class.
    """


    def get_compiler(self):
        """
        Return which thrift compiler to use.
        """

        return thrift_interface.default_get_compiler()

    def get_lang(self):
        """
        Return the language name.
        """

        raise NotImplementedError()

    def get_names(self):
        """
        Reports all languages from this converter as a frozen set.
        """
        return frozenset([self.get_lang()])

    def get_compiler_lang(self):
        """
        Return the thrift compiler language name.
        """

        return self.get_lang()

    def get_extra_includes(self, **kwargs):
        """
        Return any additional files that should be included in the exported
        thrift compiler include tree.
        """

        return thrift_interface.default_get_extra_includes(**kwargs)

    def get_postprocess_command(
            self,
            base_path,
            thrift_src,
            out_dir,
            **kwargs):
        """
        Return an additional command to run after the compiler has completed.
        Useful for adding language-specific error checking.
        """

        return thrift_interface.default_get_postprocess_command(base_path, thrift_src, out_dir, **kwargs)

    def get_additional_compiler(self):
        """
        Target of additional compiler that should be provided to the thrift1
        compiler (or None)
        """

        return thrift_interface.default_get_additional_compiler()

    def get_compiler_args(
            self,
            compiler_lang,
            flags,
            options,
            **kwargs):
        """
        Return args to pass into the compiler when generating sources.
        """

        return thrift_interface.default_get_compiler_args(compiler_lang, flags, options, **kwargs)

    def get_compiler_command(
            self,
            compiler,
            compiler_args,
            includes,
            additional_compiler):
        return thrift_interface.default_get_compiler_command(
            compiler,
            compiler_args,
            includes,
            additional_compiler,
        )

    def get_generated_sources(
            self,
            base_path,
            name,
            thrift_src,
            services,
            options,
            **kwargs):
        """
        Return a dict of all generated thrift sources, mapping the logical
        language-specific name to the path of the generated source relative
        to the thrift compiler output directory.
        """

        raise NotImplementedError()

    def get_options(self, base_path, parsed_options):
        """
        Apply any conversions to parsed language-specific thrift options.
        """

        return thrift_interface.default_get_options(base_path, parsed_options)

    def get_language_rule(
            self,
            base_path,
            name,
            thrift_srcs,
            options,
            sources,
            deps,
            visibility,
            **kwargs):
        """
        Generate the language-specific library rule (and any extra necessary
        rules).
        """

        raise NotImplementedError()


class CppThriftConverter(ThriftLangConverter):
    """
    Specializer to support generating C/C++ libraries from thrift sources.
    """

    STATIC_REFLECTION_SUFFIXES = [
        '', '_enum', '_union', '_struct', '_constant', '_service', '_types',
        '_all',
    ]

    TYPES_HEADER = 0
    TYPES_SOURCE = 1
    CLIENTS_HEADER = 2
    CLIENTS_SOURCE = 3
    SERVICES_HEADER = 4
    SERVICES_SOURCE = 5

    SUFFIXES = collections.OrderedDict([
        ('_constants.h', TYPES_HEADER),
        ('_constants.cpp', TYPES_SOURCE),
        ('_types.h', TYPES_HEADER),
        ('_types.tcc', TYPES_HEADER),
        ('_types.cpp', TYPES_SOURCE),
        ('_data.h', TYPES_HEADER),
        ('_data.cpp', TYPES_SOURCE),
        ('_layouts.h', TYPES_HEADER),
        ('_layouts.cpp', TYPES_SOURCE),
        ('_types_custom_protocol.h', TYPES_HEADER),
    ] + [
        ('_fatal%s.h' % suffix, TYPES_HEADER)
        for suffix in STATIC_REFLECTION_SUFFIXES
    ] + [
        ('AsyncClient.h', CLIENTS_HEADER),
        ('AsyncClient.cpp', CLIENTS_SOURCE),
        ('_custom_protocol.h', SERVICES_HEADER),
        ('.tcc', SERVICES_HEADER),
        ('.h', SERVICES_HEADER),
        ('.cpp', SERVICES_SOURCE),
    ])

    def __init__(self, *args, **kwargs):
        super(CppThriftConverter, self).__init__(*args, **kwargs)

    def get_additional_compiler(self):
        return config.get_thrift2_compiler()

    def get_compiler(self):
        return config.get_thrift_compiler()

    def get_lang(self):
        return 'cpp2'

    def get_compiler_lang(self):
        return 'mstch_cpp2'

    def get_options(self, base_path, parsed_options):
        options = collections.OrderedDict()
        options['include_prefix'] = base_path
        options.update(parsed_options)
        return options

    def get_static_reflection(self, options):
        return 'reflection' in options

    def get_generated_sources(
            self,
            base_path,
            name,
            thrift_src,
            services,
            options,
            **kwargs):

        thrift_base = (
            paths.split_extension(
                paths.basename(src_and_dep_helpers.get_source_name(thrift_src)))[0])

        genfiles = []

        gen_layouts = 'frozen2' in options

        genfiles.append('%s_constants.h' % (thrift_base,))
        genfiles.append('%s_constants.cpp' % (thrift_base,))
        genfiles.append('%s_types.h' % (thrift_base,))
        genfiles.append('%s_types.cpp' % (thrift_base,))
        genfiles.append('%s_data.h' % (thrift_base,))
        genfiles.append('%s_data.cpp' % (thrift_base,))
        genfiles.append('%s_types_custom_protocol.h' % (thrift_base,))

        if gen_layouts:
            genfiles.append('%s_layouts.h' % (thrift_base,))
            genfiles.append('%s_layouts.cpp' % (thrift_base,))

        if self.get_static_reflection(options):
            for suffix in self.STATIC_REFLECTION_SUFFIXES:
                genfiles.append('%s_fatal%s.h' % (thrift_base, suffix))

        genfiles.append('%s_types.tcc' % (thrift_base,))

        for service in services:
            genfiles.append('%sAsyncClient.h' % (service,))
            genfiles.append('%sAsyncClient.cpp' % (service,))
            genfiles.append('%s.h' % (service,))
            genfiles.append('%s.cpp' % (service,))
            genfiles.append('%s_custom_protocol.h' % (service,))
            genfiles.append('%s.tcc' % (service,))

        # Everything is in the 'gen-cpp2' directory
        lang = self.get_lang()
        return collections.OrderedDict(
            [(p, p) for p in
                [paths.join('gen-' + lang, path) for path in genfiles]])

    def is_header(self, src):
        _, ext = paths.split_extension(src)
        return ext in ('.h', '.tcc')

    def get_src_type(self, src):
        return next((
            type
            for suffix, type in self.SUFFIXES.items()
            if src.endswith(suffix)))

    def get_language_rule(
            self,
            base_path,
            name,
            thrift_srcs,
            options,
            sources_map,
            deps,
            cpp2_srcs=(),
            cpp2_headers=(),
            cpp2_deps=(),
            cpp2_external_deps=(),
            cpp2_compiler_flags=(),
            cpp2_compiler_specific_flags=None,
            visibility=None,
            **kwargs):
        """
        Generates a handful of rules:
            <name>-<lang>-types: A library that just has the 'types' h, tcc and
                          cpp files
            <name>-<lang>-clients: A library that just has the client and async
                                   client h and cpp files
            <name>-<lang>-services: A library that has h, tcc and cpp files
                                    needed to run a specific service
            <name>-<lang>: An uber rule for compatibility that just depends on
                           the three above rules
        This is done in order to trim down dependencies and compilation units
        when clients/services are not actually needed.
        """

        sources = thrift_common.merge_sources_map(sources_map)

        types_suffix = '-types'
        types_sources = src_and_dep_helpers.convert_source_list(base_path, cpp2_srcs)
        types_headers = src_and_dep_helpers.convert_source_list(base_path, cpp2_headers)
        types_deps = [
            thrift_common.get_thrift_dep_target('folly', 'indestructible'),
            thrift_common.get_thrift_dep_target('folly', 'optional'),
        ]
        clients_and_services_suffix = '-clients_and_services'
        clients_suffix = '-clients'
        clients_sources = []
        clients_headers = []
        services_suffix = '-services'
        services_sources = []
        services_headers = []

        clients_deps = [
            thrift_common.get_thrift_dep_target('folly/futures', 'core'),
            thrift_common.get_thrift_dep_target('folly/io', 'iobuf'),
            ':%s%s' % (name, types_suffix),
        ]
        services_deps = [
            # TODO: Remove this 'clients' dependency
            ':%s%s' % (name, clients_suffix),
            ':%s%s' % (name, types_suffix),
        ]

        # Get sources/headers for the -types, -clients and -services rules
        for filename, file_target in sources.items():
            source_type = self.get_src_type(filename)
            if source_type == self.TYPES_SOURCE:
                types_sources.append(file_target)
            elif source_type == self.TYPES_HEADER:
                types_headers.append(file_target)
            elif source_type == self.CLIENTS_SOURCE:
                clients_sources.append(file_target)
            elif source_type == self.CLIENTS_HEADER:
                clients_headers.append(file_target)
            elif source_type == self.SERVICES_SOURCE:
                services_sources.append(file_target)
            elif source_type == self.SERVICES_HEADER:
                services_headers.append(file_target)

        types_deps.extend((d + types_suffix for d in deps))
        clients_deps.extend((d + clients_suffix for d in deps))
        services_deps.extend((d + services_suffix for d in deps))

        # Add in cpp-specific deps and external_deps
        common_deps = []
        common_deps.extend(cpp2_deps)
        common_external_deps = []
        common_external_deps.extend(cpp2_external_deps)

        # Add required dependencies for Stream support
        if 'stream' in options:
            common_deps.append(
                thrift_common.get_thrift_dep_target('yarpl', 'yarpl'))
            clients_deps.append(
                thrift_common.get_thrift_dep_target(
                    'thrift/lib/cpp2/transport/core', 'thrift_client'))
            services_deps.append(
                thrift_common.get_thrift_dep_target(
                    'thrift/lib/cpp2/transport/core',
                    'thrift_processor'))
        # The 'json' thrift option will generate code that includes
        # headers from deprecated/json.  So add a dependency on it here
        # so all external header paths will also be added.
        if 'json' in options:
            common_deps.append(
                thrift_common.get_thrift_dep_target('thrift/lib/cpp', 'json_deps'))
        if 'frozen' in options:
            common_deps.append(thrift_common.get_thrift_dep_target(
                'thrift/lib/cpp', 'frozen'))
        if 'frozen2' in options:
            common_deps.append(thrift_common.get_thrift_dep_target(
                'thrift/lib/cpp2/frozen', 'frozen'))

        # any c++ rule that generates thrift files must depend on the
        # thrift lib; add that dep now if it wasn't explicitly stated
        # already
        types_deps.append(
            thrift_common.get_thrift_dep_target('thrift/lib/cpp2', 'types_deps'))
        clients_deps.append(
            thrift_common.get_thrift_dep_target('thrift/lib/cpp2', 'thrift_base'))
        services_deps.append(
            thrift_common.get_thrift_dep_target('thrift/lib/cpp2', 'thrift_base'))
        if self.get_static_reflection(options):
            common_deps.append(
                thrift_common.get_thrift_dep_target(
                    'thrift/lib/cpp2/reflection', 'reflection'))

        types_deps.extend(common_deps)
        services_deps.extend(common_deps)
        clients_deps.extend(common_deps)

        # Disable variable tracking for thrift generated C/C++ sources, as
        # it's pretty expensive and not necessarily useful (D2174972).
        common_compiler_flags = ['-fno-var-tracking']
        common_compiler_flags.extend(cpp2_compiler_flags)

        common_compiler_specific_flags = (
            cpp2_compiler_specific_flags if cpp2_compiler_specific_flags else {}
        )

        # Support a global config for explicitly opting thrift generated C/C++
        # rules in to using modules.
        modular_headers = (
            read_bool(
                "cxx",
                "modular_headers_thrift_default",
                required=False))

        # Create the types, services and clients rules
        # Delegate to the C/C++ library converting to add in things like
        # sanitizer and BUILD_MODE flags.
        cpp_library(
            name=name + types_suffix,
            srcs=types_sources,
            headers=types_headers,
            deps=types_deps,
            external_deps=common_external_deps,
            compiler_flags=common_compiler_flags,
            compiler_specific_flags=common_compiler_specific_flags,
            # TODO(T23121628): Some rules have undefined symbols (e.g. uncomment
            # and build //thrift/lib/cpp2/test:exceptservice-cpp2-types).
            undefined_symbols=True,
            visibility=visibility,
            modular_headers=modular_headers,
        )
        cpp_library(
            name=name + clients_suffix,
            srcs=clients_sources,
            headers=clients_headers,
            deps=clients_deps,
            external_deps=common_external_deps,
            compiler_flags=common_compiler_flags,
            compiler_specific_flags=common_compiler_specific_flags,
            # TODO(T23121628): Some rules have undefined symbols (e.g. uncomment
            # and build //thrift/lib/cpp2/test:Presult-cpp2-clients).
            undefined_symbols=True,
            visibility=visibility,
            modular_headers=modular_headers,
        )
        cpp_library(
            name + services_suffix,
            srcs=services_sources,
            headers=services_headers,
            deps=services_deps,
            external_deps=common_external_deps,
            compiler_flags=common_compiler_flags,
            compiler_specific_flags=common_compiler_specific_flags,
            visibility=visibility,
            modular_headers=modular_headers,
        )
        # Create a master rule that depends on -types, -services and -clients
        # for compatibility
        cpp_library(
            name,
            srcs=[],
            headers=[],
            deps=[
                ':' + name + types_suffix,
                ':' + name + clients_suffix,
                ':' + name + services_suffix,
            ],
            visibility=visibility,
            modular_headers=modular_headers,
        )

class HaskellThriftConverter(ThriftLangConverter):
    """
    Specializer to support generating Haskell libraries from thrift sources.
    """

    THRIFT_HS_LIBS = [
        target_utils.RootRuleTarget('thrift/lib/hs', 'thrift'),
        target_utils.RootRuleTarget('thrift/lib/hs', 'types'),
        target_utils.RootRuleTarget('thrift/lib/hs', 'protocol'),
        target_utils.RootRuleTarget('thrift/lib/hs', 'transport'),
    ]

    THRIFT_HS_LIBS_DEPRECATED = [
        target_utils.RootRuleTarget('thrift/lib/hs', 'hs'),
    ]

    THRIFT_HS2_LIBS = [
        target_utils.RootRuleTarget('common/hs/thrift/lib', 'codegen-types-only'),
        target_utils.RootRuleTarget('common/hs/thrift/lib', 'protocol'),
    ]

    THRIFT_HS2_SERVICE_LIBS = [
        target_utils.RootRuleTarget('common/hs/thrift/lib', 'channel'),
        target_utils.RootRuleTarget('common/hs/thrift/lib', 'codegen'),
        target_utils.RootRuleTarget('common/hs/thrift/lib', 'processor'),
        target_utils.RootRuleTarget('common/hs/thrift/lib', 'types'),
        target_utils.RootRuleTarget('common/hs/thrift/lib/if', 'application-exception-hs2')
    ]

    THRIFT_HS_PACKAGES = [
        'base',
        'bytestring',
        'containers',
        'deepseq',
        'hashable',
        'QuickCheck',
        'text',
        'unordered-containers',
        'vector',
    ]

    THRIFT_HS2_PACKAGES = [
        'aeson',
        'base',
        'binary-parsers',
        'bytestring',
        'containers',
        'data-default',
        'deepseq',
        'hashable',
        'STMonadTrans',
        'text',
        'transformers',
        'unordered-containers',
        'vector',
    ]

    def __init__(self, *args, **kwargs):
        is_hs2 = kwargs.pop('is_hs2', False)
        super(HaskellThriftConverter, self).__init__(*args, **kwargs)
        self._is_hs2 = is_hs2

    def get_compiler(self):
        if self._is_hs2:
            return config.get_thrift_hs2_compiler()
        else:
            return config.get_thrift_compiler()

    def get_lang(self):
        return 'hs2' if self._is_hs2 else 'hs'

    def get_extra_includes(self, hs_includes=(), **kwargs):
        return hs_includes

    def get_compiler_args(
            self,
            compiler_lang,
            flags,
            options,
            hs_required_symbols=None,
            **kwargs):
        """
        Return compiler args when compiling for haskell languages.
        """

        # If this isn't `hs2` fall back to getting the regular copmiler args.
        if self.get_lang() != 'hs2':
            return super(HaskellThriftConverter, self).get_compiler_args(
                compiler_lang,
                flags,
                options)

        args = ["--hs"]

        # Format the options and pass them into the hs2 compiler.
        for option, val in options.items():
            flag = '--' + option
            if val != None:
                flag += '=' + val
            args.append(flag)

        # Include rule-specific flags.
        args.extend(flags)

        # Add in the require symbols parameter.
        if hs_required_symbols != None:
            args.append('--required-symbols')
            args.append(hs_required_symbols)

        return args

    def get_generated_sources(
            self,
            base_path,
            name,
            thrift_src,
            services,
            options,
            hs_namespace=None,
            **kwargs):

        thrift_base = paths.split_extension(paths.basename(thrift_src))[0]
        thrift_base = capitalize(thrift_base)
        namespace = hs_namespace or ''
        lang = self.get_lang()

        genfiles = []

        if lang == 'hs':
            genfiles.append('%s_Consts.hs' % thrift_base)
            genfiles.append('%s_Types.hs' % thrift_base)
            for service in services:
                service = capitalize(service)
                genfiles.append('%s.hs' % service)
                genfiles.append('%s_Client.hs' % service)
                genfiles.append('%s_Iface.hs' % service)
                genfiles.append('%s_Fuzzer.hs' % service)
            namespace = namespace.replace('.', '/')

        elif lang == 'hs2':
            thrift_base = camel(thrift_base)
            namespace = '/'.join(map(camel, namespace.split('.')))
            genfiles.append('%s/Types.hs' % thrift_base)
            for service in services:
                genfiles.append('%s/%s/Client.hs' % (thrift_base, service))
                genfiles.append('%s/%s/Service.hs' % (thrift_base, service))

        return collections.OrderedDict(
            [(path, paths.join('gen-' + lang, path)) for path in
                [paths.join(namespace, genfile) for genfile in genfiles]])

    def get_language_rule(
            self,
            base_path,
            name,
            thrift_srcs,
            options,
            sources_map,
            deps,
            hs_packages=(),
            hs2_deps=[],
            visibility=None,
            **kwargs):

        platform = platform_utils.get_platform_for_base_path(base_path)

        srcs = thrift_common.merge_sources_map(sources_map)

        dependencies = []
        if not self._is_hs2:
            if 'new_deps' in options:
                dependencies.extend(self.THRIFT_HS_LIBS)
            else:
                dependencies.extend(self.THRIFT_HS_LIBS_DEPRECATED)
            dependencies.extend(haskell_rules.get_deps_for_packages(
                self.THRIFT_HS_PACKAGES, platform))
        else:
            for services in thrift_srcs.itervalues():
                if services:
                    dependencies.extend(self.THRIFT_HS2_SERVICE_LIBS)
                    break
            dependencies.extend(self.THRIFT_HS2_LIBS)
            dependencies.extend(haskell_rules.get_deps_for_packages(
                self.THRIFT_HS2_PACKAGES + (hs_packages or []), platform))
            for dep in hs2_deps:
                dependencies.append(target_utils.parse_target(dep, default_base_path=base_path))
        for dep in deps:
            dependencies.append(target_utils.parse_target(dep, default_base_path=base_path))
        deps, platform_deps = src_and_dep_helpers.format_all_deps(dependencies)
        enable_profiling = True if haskell_common.read_hs_profile() else None

        fb_native.haskell_library(
            name = name,
            visibility = visibility,
            srcs = srcs,
            deps = deps,
            platform_deps = platform_deps,
            enable_profiling = enable_profiling,
        )


class JavaDeprecatedThriftBaseConverter(ThriftLangConverter):
    """
    Specializer to support generating Java libraries from thrift sources
    using plain fbthrift or Apache Thrift.
    """

    def __init__(self, *args, **kwargs):
        super(JavaDeprecatedThriftBaseConverter, self).__init__(
            *args, **kwargs)

    def get_compiler_lang(self):
        return 'java'

    def get_generated_sources(
            self,
            base_path,
            name,
            thrift_src,
            services,
            options,
            **kwargs):

        # We want *all* the generated sources, so top-level directory.
        return collections.OrderedDict([('', 'gen-java')])

    def get_language_rule(
            self,
            base_path,
            name,
            thrift_srcs,
            options,
            sources_map,
            deps,
            javadeprecated_maven_coords=None,
            javadeprecated_maven_publisher_enabled=False,
            javadeprecated_maven_publisher_version_prefix='1.0',
            visibility=None,
            **kwargs):

        out_srcs = []

        # Pack all generated source directories into a source zip, which we'll
        # feed into the Java library rule.
        if sources_map:
            src_zip_name = name + '.src.zip'
            fb_native.zip_file(
                name = src_zip_name,
                labels = ['generated'],
                visibility = visibility,
                srcs = [
                    source
                    for sources in sources_map.values()
                    for source in sources.values()
                ],
                out = src_zip_name,
            )
            out_srcs.append(':' + src_zip_name)

        # Wrap the source zip in a java library rule, with an implicit dep on
        # the thrift library.
        out_deps = []
        out_deps.extend(deps)
        out_deps.extend(self._get_runtime_dependencies())
        java_library(
            name=name,
            srcs=out_srcs,
            duplicate_finder_enabled_DO_NOT_USE=False,
            exported_deps=out_deps,
            maven_coords=javadeprecated_maven_coords,
            maven_publisher_enabled=javadeprecated_maven_publisher_enabled,
            maven_publisher_version_prefix=(
                javadeprecated_maven_publisher_version_prefix),
            visibility=visibility)


class JavaDeprecatedThriftConverter(JavaDeprecatedThriftBaseConverter):
    """
    Specializer to support generating Java libraries from thrift sources
    using fbthrift.
    """

    def __init__(self, *args, **kwargs):
        super(JavaDeprecatedThriftConverter, self).__init__(
            *args, **kwargs)

    def get_compiler(self):
        return native.read_config(
            'thrift', 'compiler',
            super(JavaDeprecatedThriftConverter, self).get_compiler())

    def get_compiler_command(
            self,
            compiler,
            compiler_args,
            includes,
            additional_compiler):
        check_cmd = ' '.join([
            '$(exe //tools/build/buck/java:check_thrift_flavor)',
            'fb',
            '$SRCS',
        ])

        return '{} && {}'.format(
            check_cmd,
            super(JavaDeprecatedThriftBaseConverter, self).get_compiler_command(
                compiler, compiler_args, includes, additional_compiler))

    def get_lang(self):
        return 'javadeprecated'

    def _get_runtime_dependencies(self):
        return [
            '//thrift/lib/java:thrift',
            '//third-party-java/org.slf4j:slf4j-api',
        ]


class JavaDeprecatedApacheThriftConverter(JavaDeprecatedThriftBaseConverter):
    """
    Specializer to support generating Java libraries from thrift sources
    using the Apache Thrift compiler.
    """

    def __init__(self, *args, **kwargs):
        super(JavaDeprecatedApacheThriftConverter, self).__init__(
            *args, **kwargs)

    def get_lang(self):
        return 'javadeprecated-apache'

    def get_compiler(self):
        return config.get_thrift_deprecated_apache_compiler()

    def get_compiler_command(
            self,
            compiler,
            compiler_args,
            includes,
            additional_compiler):
        check_cmd = ' '.join([
            '$(exe //tools/build/buck/java:check_thrift_flavor)',
            'apache',
            '$SRCS',
        ])

        cmd = []
        cmd.append('$(exe {})'.format(compiler))
        cmd.extend(compiler_args)
        cmd.append('-I')
        cmd.append(
            '$(location {})'.format(includes))
        cmd.append('-o')
        cmd.append('"$OUT"')
        cmd.append('"$SRCS"')

        return check_cmd + ' && ' + ' '.join(cmd)

    def _get_runtime_dependencies(self):
        return [
            '//third-party-java/org.apache.thrift:libthrift',
            '//third-party-java/org.slf4j:slf4j-api',
        ]


class JsThriftConverter(ThriftLangConverter):
    """
    Specializer to support generating D libraries from thrift sources.
    """

    def __init__(self, *args, **kwargs):
        super(JsThriftConverter, self).__init__(*args, **kwargs)

    def get_lang(self):
        return 'js'

    def get_generated_sources(
            self,
            base_path,
            name,
            thrift_src,
            services,
            options,
            **kwargs):

        thrift_base = paths.split_extension(paths.basename(thrift_src))[0]

        genfiles = []
        genfiles.append('%s_types.js' % thrift_base)
        for service in services:
            genfiles.append('%s.js' % service)

        out_dir = 'gen-nodejs' if 'node' in options else 'gen-js'
        gen_srcs = collections.OrderedDict()
        for path in genfiles:
            dst = paths.join('node_modules', thrift_base, path)
            src = paths.join(out_dir, path)
            gen_srcs[dst] = src

        return gen_srcs

    def get_language_rule(
            self,
            base_path,
            name,
            thrift_srcs,
            options,
            sources_map,
            deps,
            visibility=None,
            **kwargs):

        sources = thrift_common.merge_sources_map(sources_map)

        cmds = []

        for dep in deps:
            cmds.append('rsync -a $(location {})/ "$OUT"'.format(dep))

        for dst, raw_src in sources.items():
            src = src_and_dep_helpers.get_source_name(raw_src)
            dst = paths.join('"$OUT"', dst)
            cmds.append('mkdir -p {}'.format(paths.dirname(dst)))
            cmds.append('cp {} {}'.format(paths.basename(src), dst))

        fb_native.genrule(
            name = name,
            visibility = visibility,
            out = common_paths.CURRENT_DIRECTORY,
            labels = ['generated'],
            srcs = sources.values(),
            cmd = ' && '.join(cmds),
        )


class JavaSwiftConverter(ThriftLangConverter):
    """
    Specializer to support generating Java Swift libraries from thrift sources.
    """
    tweaks = set(['EXTEND_RUNTIME_EXCEPTION'])

    def __init__(self, *args, **kwargs):
        super(JavaSwiftConverter, self).__init__(*args, **kwargs)

    def get_lang(self):
        return 'java-swift'

    def get_compiler(self):
        return config.get_thrift_swift_compiler()

    def get_compiler_args(
            self,
            compiler_lang,
            flags,
            options,
            **kwargs):
        """
        Return args to pass into the compiler when generating sources.
        """
        args = [
            '-tweak', 'ADD_CLOSEABLE_INTERFACE',
        ]
        add_thrift_exception = True
        for option in options:
            if option == 'T22418930_DO_NOT_USE_generate_beans':
                args.append('-generate_beans')
            elif option == 'T22418930_DO_NOT_USE_unadd_thrift_exception':
                add_thrift_exception = False
            elif option in JavaSwiftConverter.tweaks:
                args.append('-tweak')
                args.append(option)
            else:
                raise ValueError(
                    'the "{0}" java-swift option is invalid'.format(option))
        if add_thrift_exception:
            args.extend(['-tweak', 'ADD_THRIFT_EXCEPTION'])
        return args

    def get_compiler_command(
            self,
            compiler,
            compiler_args,
            includes,
            additional_compiler):
        cmd = []
        cmd.append('$(exe {})'.format(compiler))
        cmd.append('-include_paths')
        cmd.append(
            '$(location {})'.format(includes))
        cmd.extend(compiler_args)
        cmd.append('-out')
        # We manually set gen-swift here for the purposes of following
        # the convention in the fbthrift generator
        cmd.append('"$OUT"{}'.format('/gen-swift'))
        cmd.append('"$SRCS"')
        return ' '.join(cmd)

    def get_generated_sources(
            self,
            base_path,
            name,
            thrift_srcs,
            services,
            options,
            **kwargs):
        # we want all the sources under gen-swift
        return collections.OrderedDict([('', 'gen-swift')])

    def get_language_rule(
            self,
            base_path,
            name,
            thrift_srcs,
            options,
            sources_map,
            deps,
            java_swift_maven_coords=None,
            visibility=None,
            **kwargs):
        rules = []
        out_srcs = []

        # Pack all generated source directories into a source zip, which we'll
        # feed into the Java library rule.
        if sources_map:
            src_zip_name = name + '.src.zip'
            fb_native.zip_file(
                name = src_zip_name,
                labels = ['generated'],
                visibility = visibility,
                srcs = [
                    source
                    for sources in sources_map.values()
                    for source in sources.values()
                ],
                out = src_zip_name,
            )
            out_srcs.append(':' + src_zip_name)

        out_deps = []
        out_deps.extend(deps)
        out_deps.append('//third-party-java/com.google.guava:guava')
        out_deps.append('//third-party-java/org.apache.thrift:libthrift')
        out_deps.append(
            '//third-party-java/com.facebook.swift:swift-annotations')

        maven_publisher_enabled = False
        if java_swift_maven_coords != None:
            maven_publisher_enabled = False  # TODO(T34003348)
            expected_coords_prefix = "com.facebook.thrift:"
            if not java_swift_maven_coords.startswith(expected_coords_prefix):
                fail(
                    "java_swift_maven_coords must start with '{}'".format(expected_coords_prefix))
            expected_options = sets.make(('EXTEND_RUNTIME_EXCEPTION',))
            if not sets.is_equal(sets.make(options), expected_options):
                fail((
                    "When java_swift_maven_coords is specified, you must set" +
                    " thrift_java_swift_options = {}"
                ).format(sets.to_list(expected_options)))

        java_library(
            name=name,
            visibility=visibility,
            srcs=out_srcs,
            duplicate_finder_enabled_DO_NOT_USE=False,
            exported_deps=out_deps,
            maven_coords=java_swift_maven_coords,
            maven_publisher_enabled=maven_publisher_enabled)


class LegacyPythonThriftConverter(ThriftLangConverter):
    """
    Specializer to support generating Python libraries from thrift sources.
    """

    NORMAL = 'normal'
    TWISTED = 'twisted'
    ASYNCIO = 'asyncio'
    PYI = 'pyi'
    PYI_ASYNCIO = 'pyi-asyncio'

    THRIFT_PY_LIB_RULE_NAME = target_utils.RootRuleTarget('thrift/lib/py', 'py')
    THRIFT_PY_TWISTED_LIB_RULE_NAME = target_utils.RootRuleTarget('thrift/lib/py', 'twisted')
    THRIFT_PY_ASYNCIO_LIB_RULE_NAME = target_utils.RootRuleTarget('thrift/lib/py', 'asyncio')

    def __init__(self, *args, **kwargs):
        flavor = kwargs.pop('flavor', self.NORMAL)
        super(LegacyPythonThriftConverter, self).__init__(
            *args,
            **kwargs
        )
        self._flavor = flavor
        self._ext = '.py' if flavor not in (self.PYI, self.PYI_ASYNCIO) else '.pyi'

    def get_name(self, prefix, sep, base_module=False):
        flavor = self._flavor
        if flavor in (self.PYI, self.PYI_ASYNCIO):
            if not base_module:
                return flavor
            else:
                if flavor == self.PYI_ASYNCIO:
                    flavor = self.ASYNCIO
                else:
                    flavor = self.NORMAL

        if flavor in (self.TWISTED, self.ASYNCIO):
            prefix += sep + flavor
        return prefix

    def get_names(self):
        return frozenset([
            self.get_name('py', '-'),
            self.get_name('python', '-')])

    def get_lang(self, prefix='py'):
        return self.get_name('py', '-')

    def get_compiler_lang(self):
        if self._flavor in (self.PYI, self.PYI_ASYNCIO):
            return 'mstch_pyi'
        return 'py'

    def get_thrift_base(self, thrift_src):
        return paths.split_extension(paths.basename(thrift_src))[0]

    def get_base_module(self, **kwargs):
        """
        Get the user-specified base-module set in via the parameter in the
        `thrift_library()`.
        """

        base_module = kwargs.get(
            self.get_name('py', '_', base_module=True) + '_base_module')

        # If no asyncio/twisted specific base module parameter is present,
        # fallback to using the general `py_base_module` parameter.
        if base_module == None:
            base_module = kwargs.get('py_base_module')

        # If nothing is set, just return `None`.
        if base_module == None:
            return None

        # Otherwise, since we accept pathy base modules, normalize it to look
        # like a proper module.
        return '/'.join(base_module.split('.'))

    def get_thrift_dir(self, base_path, thrift_src, **kwargs):
        thrift_base = self.get_thrift_base(thrift_src)
        base_module = self.get_base_module(**kwargs)
        if base_module == None:
            base_module = base_path
        return paths.join(base_module, thrift_base)

    def get_postprocess_command(
            self,
            base_path,
            thrift_src,
            out_dir,
            **kwargs):

        # The location of the generated thrift files depends on the value of
        # the "namespace py" directive in the .thrift file, and we
        # unfortunately don't know what this value is.  After compilation, make
        # sure the ttypes.py file exists in the location we expect.  If not,
        # there is probably a mismatch between the base_module parameter in the
        # TARGETS file and the "namespace py" directive in the .thrift file.
        thrift_base = self.get_thrift_base(thrift_src)
        thrift_dir = self.get_thrift_dir(base_path, thrift_src, **kwargs)

        output_dir = paths.join(out_dir, 'gen-py', thrift_dir)
        ttypes_path = paths.join(output_dir, 'ttypes' + self._ext)

        msg = [
            'Compiling %s did not generate source in %s'
            % (paths.join(base_path, thrift_src), ttypes_path)
        ]
        if self._flavor == self.ASYNCIO or self._flavor == self.PYI_ASYNCIO:
            py_flavor = 'py.asyncio'
        elif self._flavor == self.TWISTED:
            py_flavor = 'py.twisted'
        else:
            py_flavor = 'py'
        msg.append(
            'Does the "\\"namespace %s\\"" directive in the thrift file '
            'match the base_module specified in the TARGETS file?' %
            (py_flavor,))
        base_module = self.get_base_module(**kwargs)
        if base_module == None:
            base_module = base_path
            msg.append(
                '  base_module not specified, assumed to be "\\"%s\\""' %
                (base_path,))
        else:
            msg.append('  base_module is "\\"%s\\""' % (base_module,))

        expected_ns = [p for p in base_module.split('/') if p]
        expected_ns.append(thrift_base)
        expected_ns = '.'.join(expected_ns)
        msg.append(
            '  thrift file should contain "\\"namespace %s %s\\""' %
            (py_flavor, expected_ns,))

        cmd = 'if [ ! -f %s ]; then ' % (ttypes_path,)
        for line in msg:
            cmd += ' echo "%s" >&2;' % (line,)
        cmd += ' false; fi'

        return cmd

    def get_options(self, base_path, parsed_options):
        options = collections.OrderedDict()

        # We always use new style for non-python3.
        if 'new_style' in parsed_options:
            raise ValueError(
                'the "new_style" thrift python option is redundant')

        # Add flavor-specific option.
        if self._flavor == self.TWISTED:
            options['twisted'] = None
        elif self._flavor in (self.ASYNCIO, self.PYI_ASYNCIO):
            options['asyncio'] = None

        # Always use "new_style" classes.
        options['new_style'] = None

        options.update(parsed_options)

        return options

    def get_generated_sources(
            self,
            base_path,
            name,
            thrift_src,
            services,
            options,
            **kwargs):

        thrift_base = self.get_thrift_base(thrift_src)
        thrift_dir = self.get_thrift_dir(base_path, thrift_src, **kwargs)

        genfiles = []

        genfiles.append('constants' + self._ext)
        genfiles.append('ttypes' + self._ext)

        for service in services:
            # "<service>.py" and "<service>-remote" are generated for each
            # service
            genfiles.append(service + self._ext)
            if self._flavor == self.NORMAL:
                genfiles.append(service + '-remote')

        def add_ext(path, ext):
            if not path.endswith(ext):
                path += ext
            return path

        return collections.OrderedDict(
            [(add_ext(paths.join(thrift_base, path), self._ext),
              paths.join('gen-py', thrift_dir, path)) for path in genfiles])

    def get_pyi_dependency(self, name):
        if name.endswith('-asyncio'):
            name = name[:-len('-asyncio')]
        if name.endswith('-py'):
            name = name[:-len('-py')]
        if self._flavor == self.ASYNCIO:
            return name + '-pyi-asyncio'
        else:
            return name + '-pyi'

    def get_language_rule(
            self,
            base_path,
            name,
            thrift_srcs,
            options,
            sources_map,
            deps,
            visibility,
            **kwargs):

        srcs = thrift_common.merge_sources_map(sources_map)
        base_module = self.get_base_module(**kwargs)

        out_deps = []
        out_deps.extend(deps)

        # If this rule builds thrift files, automatically add a dependency
        # on the python thrift library.
        out_deps.append(target_utils.target_to_label(self.THRIFT_PY_LIB_RULE_NAME))

        # If thrift files are build with twisted support, add also
        # dependency on the thrift's twisted transport library.
        if self._flavor == self.TWISTED or 'twisted' in options:
            out_deps.append(
                target_utils.target_to_label(self.THRIFT_PY_TWISTED_LIB_RULE_NAME))

        # If thrift files are build with asyncio support, add also
        # dependency on the thrift's asyncio transport library.
        if self._flavor == self.ASYNCIO or 'asyncio' in options:
            out_deps.append(
                target_utils.target_to_label(self.THRIFT_PY_ASYNCIO_LIB_RULE_NAME))

        if self._flavor in (self.NORMAL, self.ASYNCIO):
            out_deps.append(':' + self.get_pyi_dependency(name))
            has_types = True
        else:
            has_types = False

        if get_typing_config_target():
            if has_types:
                gen_typing_config(
                    name,
                    base_module if base_module != None else base_path,
                    srcs.keys(),
                    out_deps,
                    typing=True,
                    visibility=visibility,
                )
            else:
                gen_typing_config(name)

        fb_native.python_library(
            name = name,
            visibility = visibility,
            srcs = srcs,
            base_module = base_module,
            deps = out_deps,
        )


class OCamlThriftConverter(ThriftLangConverter):
    """
    Specializer to support generating OCaml libraries from thrift sources.
    """

    THRIFT_OCAML_LIBS = [
        target_utils.RootRuleTarget('common/ocaml/thrift', 'thrift'),
    ]

    THRIFT_OCAML_DEPS = [
        target_utils.RootRuleTarget('hphp/hack/src/third-party/core', 'core'),
    ]

    def __init__(self, *args, **kwargs):
        super(OCamlThriftConverter, self).__init__(*args, **kwargs)

    def get_compiler(self):
        return config.get_thrift_ocaml_compiler()

    def get_lang(self):
        return 'ocaml2'

    def get_extra_includes(self, **kwargs):
        return []

    def get_compiler_args(
            self,
            compiler_lang,
            flags,
            options,
            **kwargs):
        """
        Return compiler args when compiling for ocaml.
        """

        args = []

        # The OCaml compiler relies on the HS2 compiler to parse .thrift sources to JSON
        args.append('-c')
        args.append('$(exe {})'.format(config.get_thrift_hs2_compiler()))

        # Format the options and pass them into the ocaml compiler.
        for option, val in options.items():
            flag = '--' + option
            if val != None:
                flag += '=' + val
            args.append(flag)

        # Include rule-specific flags.
        args.extend(flags)

        return args

    def get_generated_sources(
            self,
            base_path,
            name,
            thrift_src,
            services,
            options,
            **kwargs):

        thrift_base = paths.split_extension(paths.basename(thrift_src))[0]
        thrift_base = capitalize(thrift_base)

        genfiles = []

        genfiles.append('%s_consts.ml' % thrift_base)
        genfiles.append('%s_types.ml' % thrift_base)
        for service in services:
            service = capitalize(service)
            genfiles.append('%s.ml' % service)

        return collections.OrderedDict(
            [(path, path) for path in genfiles])

    def get_language_rule(
            self,
            base_path,
            name,
            thrift_srcs,
            options,
            sources_map,
            deps,
            visibility,
            **kwargs):

        dependencies = []
        dependencies.extend(self.THRIFT_OCAML_DEPS)
        dependencies.extend(self.THRIFT_OCAML_LIBS)
        for dep in deps:
            dependencies.append(target_utils.parse_target(dep, default_base_path=base_path))

        fb_native.ocaml_library(
            name=name,
            visibility=get_visibility(visibility, name),
            srcs=thrift_common.merge_sources_map(sources_map).values(),
            deps=(src_and_dep_helpers.format_all_deps(dependencies))[0],
        )


class ThriftLibraryConverter(base.Converter):

    def __init__(self):
        super(ThriftLibraryConverter, self).__init__()

        # Setup the macro converters.
        converters = [
            CppThriftConverter(),
            d_thrift_converter,
            go_thrift_converter,
            HaskellThriftConverter(is_hs2=False),
            HaskellThriftConverter(is_hs2=True),
            JsThriftConverter(),
            OCamlThriftConverter(),
            rust_thrift_converter,
            thriftdoc_python_thrift_converter,
            python3_thrift_converter,
            LegacyPythonThriftConverter(
                flavor=LegacyPythonThriftConverter.NORMAL),
            LegacyPythonThriftConverter(
                flavor=LegacyPythonThriftConverter.ASYNCIO),
            LegacyPythonThriftConverter(
                flavor=LegacyPythonThriftConverter.TWISTED),
            LegacyPythonThriftConverter(
                flavor=LegacyPythonThriftConverter.PYI),
            LegacyPythonThriftConverter(
                flavor=LegacyPythonThriftConverter.PYI_ASYNCIO),
            JavaDeprecatedApacheThriftConverter(),
            JavaDeprecatedThriftConverter(),
            JavaSwiftConverter(),
        ]
        self._converters = {}
        self._name_to_lang = {}
        for converter in converters:
            self._converters[converter.get_lang()] = converter
            for name in converter.get_names():
                self._name_to_lang[name] = converter.get_lang()

    def get_fbconfig_rule_type(self):
        return 'thrift_library'

    def get_buck_rule_type(self):
        return 'thrift_library'

    def get_languages(self, names):
        """
        Convert the `languages` parameter to a normalized list of languages.
        """

        languages = set()

        if names == None:
            raise TypeError('thrift_library() requires languages argument')

        for name in names:
            lang = self._name_to_lang.get(name)
            if lang == None:
                raise TypeError(
                    'thrift_library() does not support language {!r}'
                    .format(name))
            if lang in languages:
                raise TypeError(
                    'thrift_library() given duplicate language {!r}'
                    .format(lang))
            languages.add(lang)

        return languages

    def parse_thrift_options(self, options):
        """
        Parse the option list or string into a dict.
        """

        parsed = collections.OrderedDict()

        if isinstance(options, basestring):
            options = options.split(',')

        for option in options:
            if '=' in option:
                option, val = option.rsplit('=', 1)
                parsed[option] = val
            else:
                parsed[option] = None

        return parsed

    def parse_thrift_args(self, args):
        """
        For some reason we accept `thrift_args` as either a list or
        space-separated string.
        """

        if isinstance(args, basestring):
            args = args.split()

        return args

    def get_thrift_options(self, options):
        if isinstance(options, basestring):
            options = options.split(',')
        return options

    def fixup_thrift_srcs(self, srcs):
        new_srcs = collections.OrderedDict()
        for name, services in sorted(srcs.items()):
            if services == None:
                services = []
            elif not isinstance(services, (tuple, list)):
                services = [services]
            new_srcs[name] = services
        return new_srcs

    def get_exported_include_tree(self, dep):
        """
        Generate the exported thrift source includes target use for the given
        thrift library target.
        """

        return dep + '-thrift-includes'

    def generate_compile_rule(
            self,
            base_path,
            name,
            compiler,
            lang,
            compiler_args,
            source,
            postprocess_cmd=None,
            visibility=None):
        """
        Generate a rule which runs the thrift compiler for the given inputs.
        """

        genrule_name = (
            '{}-{}-{}'.format(name, lang, src_and_dep_helpers.get_source_name(source)))
        cmds = []
        converter = self._converters[lang]
        cmds.append(
            converter.get_compiler_command(
                compiler,
                compiler_args,
                self.get_exported_include_tree(':' + name),
                converter.get_additional_compiler()))

        if postprocess_cmd != None:
            cmds.append(postprocess_cmd)

        fb_native.genrule(
            name = genrule_name,
            labels = ['generated'],
            visibility = visibility,
            out = common_paths.CURRENT_DIRECTORY,
            srcs = [source],
            cmd = ' && '.join(cmds),
        )
        return genrule_name

    def generate_generated_source_rules(self, compile_name, srcs, visibility):
        """
        Create rules to extra individual sources out of the directory of thrift
        sources the compiler generated.
        """

        out = collections.OrderedDict()
        rules = []

        for name, src in srcs.items():
            cmd = ' && '.join([
                'mkdir -p `dirname $OUT`',
                'cp -R $(location :{})/{} $OUT'.format(compile_name, src),
            ])
            genrule_name = '{}={}'.format(compile_name, src)
            fb_native.genrule(
                name = genrule_name,
                labels = ['generated'],
                visibility = visibility,
                out = src,
                cmd = cmd,
            )
            out[name] = ':' + genrule_name

        return out

    def convert_macros(
            self,
            base_path,
            name,
            thrift_srcs={},
            thrift_args=(),
            deps=(),
            external_deps=(),
            languages=None,
            visibility=None,
            plugins=[],
            **kwargs):
        """
        Thrift library conversion implemented purely via macros (i.e. no Buck
        support).
        """

        # Parse incoming options.
        thrift_srcs = self.fixup_thrift_srcs(thrift_srcs)
        thrift_args = self.parse_thrift_args(thrift_args)
        languages = self.get_languages(languages)
        deps = [src_and_dep_helpers.convert_build_target(base_path, d) for d in deps]

        # Setup the exported include tree to dependents.
        includes = set()
        includes.update(thrift_srcs.keys())
        for lang in languages:
            converter = self._converters[lang]
            includes.update(converter.get_extra_includes(**kwargs))

        merge_tree(
            base_path,
            self.get_exported_include_tree(name),
            sorted(includes),
            map(self.get_exported_include_tree, deps),
            labels=["generated"],
            visibility=visibility)

        # py3 thrift requires cpp2
        if 'py3' in languages and 'cpp2' not in languages:
            languages.add('cpp2')

        # save cpp2_options for later use by 'py3'
        if 'cpp2' in languages:
            cpp2_options = (
                self.parse_thrift_options(
                    kwargs.get('thrift_cpp2_options', ())))

        # Types are generated for all legacy Python Thrift
        if 'py' in languages:
            languages.add('pyi')
            # Save the options for pyi to use
            py_options = (self.parse_thrift_options(
                kwargs.get('thrift_py_options', ())
            ))

        if 'py-asyncio' in languages:
            languages.add('pyi-asyncio')
            # Save the options for pyi to use
            py_asyncio_options = (self.parse_thrift_options(
                kwargs.get('thrift_py_asyncio_options', ())
            ))

        # Generate rules for all supported languages.
        for lang in languages:
            converter = self._converters[lang]
            compiler = converter.get_compiler()
            options = (
                self.parse_thrift_options(
                    kwargs.get('thrift_{}_options'.format(
                        lang.replace('-', '_')), ())))
            if lang == "pyi":
                options.update(py_options)
            if lang == "pyi-asyncio":
                options.update(py_asyncio_options)
            if lang == 'py3':
                options.update(cpp2_options)

            compiler_args = converter.get_compiler_args(
                converter.get_compiler_lang(),
                thrift_args,
                converter.get_options(base_path, options),
                **kwargs)

            all_gen_srcs = collections.OrderedDict()
            for thrift_src, services in thrift_srcs.items():
                thrift_name = src_and_dep_helpers.get_source_name(thrift_src)

                # Generate the thrift compile rules.
                compile_rule_name = (
                    self.generate_compile_rule(
                        base_path,
                        name,
                        compiler,
                        lang,
                        compiler_args,
                        thrift_src,
                        converter.get_postprocess_command(
                            base_path,
                            thrift_name,
                            '$OUT',
                            **kwargs),
                        visibility=visibility))

                # Create wrapper rules to extract individual generated sources
                # and expose via target refs in the UI.
                gen_srcs = (
                    converter.get_generated_sources(
                        base_path,
                        name,
                        thrift_name,
                        services,
                        options,
                        visibility=visibility,
                        **kwargs))
                gen_srcs = self.generate_generated_source_rules(
                    compile_rule_name,
                    gen_srcs,
                    visibility=visibility
                )
                all_gen_srcs[thrift_name] = gen_srcs

            # Generate rules from Thrift plugins
            for plugin in plugins:
                plugin.generate_rules(
                    plugin,
                    base_path,
                    name,
                    lang,
                    thrift_srcs,
                    compiler_args,
                    self.get_exported_include_tree(':' + name),
                    deps,
                )
            # Generate the per-language rules.
            converter.get_language_rule(
                base_path,
                name + '-' + lang,
                thrift_srcs,
                options,
                all_gen_srcs,
                [dep + '-' + lang for dep in deps],
                visibility=visibility,
                **kwargs)

    def get_allowed_args(self):
        """
        Return the list of allowed arguments.
        """

        allowed_args = set([
            'cpp2_compiler_flags',
            'cpp2_compiler_specific_flags',
            'cpp2_deps',
            'cpp2_external_deps',
            'cpp2_headers',
            'cpp2_srcs',
            'd_thrift_namespaces',
            'deps',
            'go_pkg_base_path',
            'go_thrift_namespaces',
            'go_thrift_src_inter_deps',
            'hs_includes',
            'hs_namespace',
            'hs_packages',
            'hs_required_symbols',
            'hs2_deps',
            'java_deps',
            'javadeprecated_maven_coords',
            'javadeprecated_maven_publisher_enabled',
            'javadeprecated_maven_publisher_version_prefix',
            'java_swift_maven_coords',
            'languages',
            'name',
            'plugins',
            'py_asyncio_base_module',
            'py_base_module',
            'py_remote_service_router',
            'py_twisted_base_module',
            'py3_namespace',
            'ruby_gem_name',
            'ruby_gem_require_paths',
            'ruby_gem_version',
            'thrift_args',
            'thrift_srcs',
        ])

        # Add the default args based on the languages we support
        langs = []
        langs.extend(self._name_to_lang.values())
        langs.extend([
            'py',
            'py-asyncio',
            'py-twisted',
            'ruby',
        ])
        for lang in langs:
            allowed_args.add('thrift_' + lang.replace('-', '_') + '_options')

        return allowed_args

    def convert(self, base_path, name=None, languages=None, visibility=None, **kwargs):
        visibility = get_visibility(visibility, name)

        supported_languages = read_list(
            'thrift', 'supported_languages', delimiter=None, required=False,
        )
        if supported_languages != None:
            languages = set(languages) & set(supported_languages)

        # Convert rules we support via macros.
        macro_languages = self.get_languages(languages)
        if macro_languages:
            self.convert_macros(base_path, name=name, languages=languages, visibility=visibility, **kwargs)

        # If python is listed in languages, then also generate the py-remote
        # rules.
        # TODO: Move this logic into convert_macros
        if 'py' in languages or 'python' in languages:
            py_remote_binaries(
                base_path,
                name=name,
                thrift_srcs=self.fixup_thrift_srcs(kwargs.get('thrift_srcs', {})),
                base_module=kwargs.get('py_base_module'),
                include_sr=kwargs.get('py_remote_service_router', False),
                visibility=visibility)

        return []
