load("@fbcode_macros//build_defs/lib:cpp_common.bzl", "cpp_common")
load("@fbcode_macros//build_defs/lib:python_typing.bzl", "gen_typing_config")
load("@fbcode_macros//build_defs/lib:target_utils.bzl", "target_utils")
load("@fbcode_macros//build_defs/lib:visibility.bzl", "get_visibility")
load("@fbsource//tools/build_defs:fb_native_wrapper.bzl", "fb_native")

_PYTHON_EXTENSION_DEPS = [target_utils.ThirdPartyRuleTarget("python", "python")]

def cpp_python_extension(
        name,
        typing_rule_name_prefix = None,
        arch_compiler_flags = None,  # {}
        arch_preprocessor_flags = None,  # {}
        auto_headers = None,
        compiler_flags = (),
        compiler_specific_flags = None,  # {}
        deps = (),
        external_deps = (),
        global_symbols = (),
        header_namespace = None,
        headers = None,
        known_warnings = (),  # True or list
        lex_args = (),
        linker_flags = (),
        modules = None,
        nodefaultlibs = False,
        nvcc_flags = (),
        precompiled_header = None,
        preprocessor_flags = (),
        shared_system_deps = None,
        srcs = (),
        supports_coverage = None,
        system_include_paths = None,
        visibility = None,
        yacc_args = (),
        additional_coverage_targets = (),
        autodeps_keep = None,  # Ignore; used only by autodeps tooling.
        tags = (),
        base_module = None,
        tests = None,
        module_name = None):  # Not intended for use by end-users
    visibility = get_visibility(visibility, name)

    attrs = cpp_common.convert_cpp(
        name = name,
        cpp_rule_type = "cpp_python_extension",
        buck_rule_type = "cxx_python_extension",
        is_library = False,
        is_buck_binary = False,
        is_test = False,
        is_deployable = False,
        rule_specific_deps = _PYTHON_EXTENSION_DEPS,
        arch_compiler_flags = arch_compiler_flags or {},
        arch_preprocessor_flags = arch_preprocessor_flags or {},
        auto_headers = auto_headers,
        compiler_flags = compiler_flags,
        compiler_specific_flags = compiler_specific_flags or {},
        deps = deps,
        external_deps = external_deps,
        global_symbols = global_symbols,
        header_namespace = header_namespace,
        headers = headers,
        known_warnings = known_warnings,  # True or list
        lex_args = lex_args,
        linker_flags = linker_flags,
        modules = modules,
        nodefaultlibs = nodefaultlibs,
        nvcc_flags = nvcc_flags,
        precompiled_header = precompiled_header,
        preprocessor_flags = preprocessor_flags,
        shared_system_deps = shared_system_deps,
        srcs = srcs,
        supports_coverage = supports_coverage,
        system_include_paths = system_include_paths,
        visibility = visibility,
        yacc_args = yacc_args,
        additional_coverage_targets = additional_coverage_targets,
        autodeps_keep = autodeps_keep,  # Ignore; used only by autodeps tooling.
        tags = tags,
        base_module = base_module,
        tests = tests,
        module_name = module_name,
    )

    fb_native.cxx_python_extension(**attrs)

    # Generate an empty typing_config
    gen_typing_config(typing_rule_name_prefix or name, visibility = visibility, labels = ["generated"])
