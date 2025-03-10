#ifndef RELAY_H
#define RELAY_H

#include "constants.h"
#include "errors.h"
#include "preprocessor_macros.h"

#define RELAY_CHECK_PTR(ptr, checking_result)            \
    if (!ptr)                                            \
    {                                                    \
        RELAY_DEBUG_MSG("Detected NULL pointer")         \
        _setGlobalError(RELAY_ERROR_INVALID_PARAMETER);  \
        checking_result = RELAY_ERR;                     \
    }                                                    \
    else                                                 \
        checking_result = RELAY_OK;

#define RELAY_CHECK_PTR_WITH_RETURN(ptr)       \
    do                                         \
    {                                          \
        int checking_result = RELAY_OK;        \
        RELAY_CHECK_PTR(ptr, checking_result)  \
        if (checking_result == RELAY_ERR)      \
            return checking_result;            \
    } while (0)

RELAY_BEGIN_DECLS

/**
 * @struct Config
 * @brief Structure containing essential parameters for establishing a
 * connection with the relay via MODBUS-RTU.
 */
	typedef struct
{
	char* port;   ///< Serial port (e.g., "/dev/ttyUSB0" on Linux or "COM3" on Windows).
	int baudrate; ///< Baud rate for serial communication (e.g., 9600, 19200, 38400).
	int slave_id; ///< MODBUS device ID of the relay (default is often 1).
	int timeout;  ///< Timeout for response (in milliseconds).
} Config;

/**
 * @struct Handle
 * @brief Internal handle that stores the communication context.
 */
typedef struct
{
	void* modbus_ctx; ///< Pointer to the libmodbus context used for communication.
} Handle;

/**
 * @brief Initializes and establishes a connection to the relay.
 *
 * This function sets up a MODBUS-RTU connection over the specified serial port,
 * configures the communication settings (baud rate, slave ID, and timeout), and attempts
 * to connect to the device. On success, the provided handle is populated with the
 * communication context.
 *
 * @param config Pointer to a Config structure containing connection parameters.
 * @param handle Pointer to a Handle structure that will be populated upon success.
 * @return OK if the connection is successfully established, otherwise an error code.
 *
 * @note If an error occurs during connection, the global error variable is set accordingly.
 */
RELAY_API int Init(const Config* RELAY_RESTRICT config, Handle* RELAY_RESTRICT handle);

/**
 * @brief Turns on the relay.
 *
 * This function writes a value of 1 to the MODBUS register designated for turning the relay on.
 *
 * @param handle Pointer to an initialized Handle structure.
 * @return OK if the command is successfully executed, otherwise an error code.
 *
 * @note The function validates that the handle and the underlying MODBUS context are not NULL.
 */
RELAY_API int TurnOn(Handle* RELAY_RESTRICT handle);

/**
 * @brief Turns off the relay.
 *
 * This function writes a value of 0 to the MODBUS register designated for turning the relay off.
 *
 * @param handle Pointer to an initialized Handle structure.
 * @return OK if the command is successfully executed, otherwise an error code.
 *
 * @note The function validates that the handle and the underlying MODBUS context are not NULL.
 */
RELAY_API int TurnOff(Handle* RELAY_RESTRICT handle);

/**
 * @brief Closes the connection to the relay and frees resources.
 *
 * This function terminates the MODBUS-RTU communication session and releases any allocated memory
 * or handles associated with the connection.
 *
 * @param handle Pointer to an initialized Handle structure.
 */
RELAY_API void Close(Handle* RELAY_RESTRICT handle);

/**
 * @brief Retrieves the description of the last error encountered in the RELAY RELAY_API.
 *
 * This function returns a human-readable string describing the last error that occurred,
 * which can be useful for debugging and logging purposes.
 *
 * @return A constant character string containing the error message.
 */
RELAY_API const char* Relay_GetLastError();

RELAY_END_DECLS

#endif // !RELAY_H
