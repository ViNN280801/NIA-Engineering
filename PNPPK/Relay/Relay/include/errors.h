#ifndef ERRORS_H
#define ERRORS_H

/**
 * @def MODBUS_ERR
 * @brief General error code for libmodbus failures.
 */
#define MODBUS_ERR -1

/**
 * @brief Global variable to store the last occurred error code.
 */
extern int GlobalError;

/**
 * @def RELAY_OK
 * @brief No error occurred.
 */
#define RELAY_OK 0

/**
 * @def ERR
 * @brief General error. Base to compose other error types.
 */
#define RELAY_ERR -1

/**
 * @def RELAY_ERROR_FAILED_CONNECT
 * @brief Connection to the MODBUS device failed.
 */
#define RELAY_ERROR_FAILED_CONNECT -6001

/**
 * @def RELAY_ERROR_FAILED_CREATE_CONTEXT
 * @brief Failed to create a MODBUS-RTU context.
 */
#define RELAY_ERROR_FAILED_CREATE_CONTEXT -6002

/**
 * @def RELAY_ERROR_FAILED_SET_SLAVE
 * @brief Failed to set MODBUS slave ID.
 */
#define RELAY_ERROR_FAILED_SET_SLAVE -6003

/**
 * @def RELAY_ERROR_FAILED_SET_TIMEOUT
 * @brief Failed to set MODBUS response timeout.
 */
#define RELAY_ERROR_FAILED_SET_TIMEOUT -6004

/**
 * @def RELAY_ERROR_FAILED_WRITE_REGISTER
 * @brief Failed to write a MODBUS register.
 */
#define RELAY_ERROR_FAILED_WRITE_REGISTER -6005

/**
 * @def RELAY_ERROR_INVALID_PARAMETER
 * @brief An invalid parameter was passed to the function.
 */
#define RELAY_ERROR_INVALID_PARAMETER -6006

/// @brief Resets the global 'GlobalError' to the status RELAY_OK.
static inline void _resetGlobalError() { GlobalError = RELAY_OK; }

/// @brief Sets the global 'GlobalError' to the specified error status.
static inline void _setGlobalError(int RELAY_ERROR_code) { GlobalError = RELAY_ERROR_code; }

#endif // !ERRORS_H
