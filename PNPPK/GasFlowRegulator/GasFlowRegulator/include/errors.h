#ifndef ERRORS_H
#define ERRORS_H

/**
 * @def MODBUS_ERR
 * @brief General GlobalError code for libmodbus failures.
 */
#define MODBUS_ERR -1

/**
 * @brief Global variable to store the last occurred GlobalError code.
 */
extern int GlobalError;

/**
 * @def GAS_FLOW_REGULATOR_OK
 * @brief No GlobalError occurred.
 */
#define GAS_FLOW_REGULATOR_OK 0

/**
 * @def GAS_FLOW_REGULATOR_ERR
 * @brief General GlobalError. Base to compose other GlobalError types.
 */
#define GAS_FLOW_REGULATOR_ERR -1

/**
 * @def GAS_FLOW_REGULATOR_ERROR_FAILED_CONNECT
 * @brief Connection to the MODBUS device failed.
 */
#define GAS_FLOW_REGULATOR_ERROR_FAILED_CONNECT -1001

/**
 * @def GAS_FLOW_REGULATOR_ERROR_FAILED_CREATE_CONTEXT
 * @brief Failed to create a MODBUS-RTU context.
 */
#define GAS_FLOW_REGULATOR_ERROR_FAILED_CREATE_CONTEXT -1002

/**
 * @def GAS_FLOW_REGULATOR_ERROR_FAILED_SET_SLAVE
 * @brief Failed to set MODBUS slave ID.
 */
#define GAS_FLOW_REGULATOR_ERROR_FAILED_SET_SLAVE -1003

/**
 * @def GAS_FLOW_REGULATOR_ERROR_FAILED_SET_TIMEOUT
 * @brief Failed to set MODBUS response timeout.
 */
#define GAS_FLOW_REGULATOR_ERROR_FAILED_SET_TIMEOUT -1004

/**
 * @def GAS_FLOW_REGULATOR_ERROR_FAILED_READ_REGISTER
 * @brief Failed to read a MODBUS register.
 */
#define GAS_FLOW_REGULATOR_ERROR_FAILED_READ_REGISTER -1005

/**
 * @def GAS_FLOW_REGULATOR_ERROR_FAILED_WRITE_REGISTER
 * @brief Failed to write a MODBUS register.
 */
#define GAS_FLOW_REGULATOR_ERROR_FAILED_WRITE_REGISTER -1006

/**
 * @def GAS_FLOW_REGULATOR_ERROR_INVALID_PARAMETER
 * @brief An invalid parameter was passed to the function.
 */
#define GAS_FLOW_REGULATOR_ERROR_INVALID_PARAMETER -1007

/// @brief Resets the global 'GlobalGlobalError' to the status GAS_FLOW_REGULATOR_OK.
static inline void _resetGlobalError() { GlobalError = GAS_FLOW_REGULATOR_OK; }

/// @brief Sets the global 'GlobalGlobalError' to the specified GlobalError status.
static inline void _setGlobalError(int GAS_FLOW_REGULATOR_ERROR_code) { GlobalError = GAS_FLOW_REGULATOR_ERROR_code; }

#endif // !ERRORS_H
