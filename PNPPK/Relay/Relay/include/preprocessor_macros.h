#ifndef PREPROCESSOR_MACROS_H
#define PREPROCESSOR_MACROS_H

/* Cross-platform definition of the `restrict` keyword for compiler
 * optimization. */
#if defined(_MSC_VER)
#define RELAY_RESTRICT __restrict
#elif defined(__GNUC__) || defined(__clang__)
#define RELAY_RESTRICT __restrict__
#else
#define RELAY_RESTRICT
#endif

 /* Cross-platform shared library export macros */
#if defined(_MSC_VER) // Windows (Microsoft Visual Studio)
#if defined(DLL_EXPORTS)
#define RELAY_API __declspec(dllexport)
#else
#define RELAY_API __declspec(dllimport)
#endif
#else // Linux/macOS
#define RELAY_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
#define RELAY_BEGIN_DECLS extern "C" {
#define RELAY_END_DECLS }
#else
#define RELAY_BEGIN_DECLS
#define RELAY_END_DECLS
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

#define RELAY_DEBUG_FMT "RELAY DEBUG: [File: %s, Line: %d, Function: %s]"
#define RELAY_DEBUG_ARGS __FILE__, __LINE__, COMMON_PRETTY_FUNC

#ifdef DEBUG
#define MODBUS_DEBUG_MSG                                  \
    fprintf(stderr, DEBUG_FMT ": %s\n", DEBUG_ARGS,       \
            modbus_strerror(errno));
#define DEBUG_MSG(msg)                                    \
    fprintf(stderr, DEBUG_FMT ": %s\n", DEBUG_ARGS, msg);
#define DEBUG_GET_LAST_ERR                                \
    fprintf(stderr, DEBUG_FMT ": %s\n", DEBUG_ARGS,       \
            Relay_GetLastError());
#else
#define MODBUS_DEBUG_MSG
#define RELAY_DEBUG_MSG(msg)
#define RELAY_DEBUG_GET_LAST_ERR
#endif

#endif // !PREPROCESSOR_MACROS_H
