#ifndef PREPROCESSOR_MACROS_H
#define PREPROCESSOR_MACROS_H

/* Cross-platform definition of the `restrict` keyword for compiler optimization. */
#if defined(_MSC_VER)
#define GAS_FLOW_REGULATOR_RESTRICT __restrict
#elif defined(__GNUC__) || defined(__clang__)
#define GAS_FLOW_REGULATOR_RESTRICT __restrict__
#else
#define GAS_FLOW_REGULATOR_RESTRICT
#endif

/* Cross-platform shared library export macros */
#if defined(_MSC_VER) // Windows (Microsoft Visual Studio)
#if defined(DLL_EXPORTS)
#define GAS_FLOW_REGULATOR_API __declspec(dllexport)
#else
#define GAS_FLOW_REGULATOR_API __declspec(dllimport)
#endif
#else // Linux/macOS
#define GAS_FLOW_REGULATOR_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
#define GAS_FLOW_REGULATOR_BEGIN_DECLS \
    extern "C"                         \
    {
#define GAS_FLOW_REGULATOR_END_DECLS }
#else
#define GAS_FLOW_REGULATOR_BEGIN_DECLS
#define GAS_FLOW_REGULATOR_END_DECLS
#endif

#ifdef __linux__
#define COMMON_PRETTY_FUNC __PRETTY_FUNCTION__
#elif defined(_WIN32)
#define COMMON_PRETTY_FUNC __FUNCSIG__
#else
#define COMMON_PRETTY_FUNC __func__
#endif

#define STRINGIFY(x) STRINGIFY_IMPL(x)
#define STRINGIFY_IMPL(x) #x

#define GAS_FLOW_REGULATOR_DEBUG_FMT "GAS FLOW REGULATOR DEBUG: [File: %s, Line: %d, Function: %s]"
#define GAS_FLOW_REGULATOR_DEBUG_ARGS __FILE__, __LINE__, COMMON_PRETTY_FUNC

#ifdef GAS_FLOW_REGULATOR_DEBUG
#define MODBUS_DEBUG_MSG fprintf(stderr, GAS_FLOW_REGULATOR_DEBUG_FMT ": %s\n", GAS_FLOW_REGULATOR_DEBUG_ARGS, modbus_strerror(errno));
#define GAS_FLOW_REGULATOR_DEBUG_MSG(msg) fprintf(stderr, GAS_FLOW_REGULATOR_DEBUG_FMT ": %s\n", GAS_FLOW_REGULATOR_DEBUG_ARGS, msg);
#define GAS_FLOW_REGULATOR_DEBUG_GET_LAST_ERR fprintf(stderr, GAS_FLOW_REGULATOR_DEBUG_FMT ": %s\n", GAS_FLOW_REGULATOR_DEBUG_ARGS, GasFlowRegulator_GetLastError());
#else
#define MODBUS_DEBUG_MSG
#define GAS_FLOW_REGULATOR_DEBUG_MSG(msg)
#define GAS_FLOW_REGULATOR_DEBUG_GET_LAST_ERR
#endif

#endif // !PREPROCESSOR_MACROS_H
