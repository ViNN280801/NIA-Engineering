#ifndef GAS_FLOW_REGULATOR_H
#define GAS_FLOW_REGULATOR_H

#include "constants.h"
#include "errors.h"
#include "preprocessor_macros.h"

/**
 * @def GAS_FLOW_REGULATOR_CHECK_PTR(ptr, checking_result)
 * @brief Macro for validating a pointer and handling null values.
 *
 * This macro is designed to check whether a given pointer is valid (i.e., not `NULL`).
 * If the pointer is `NULL`, it logs a debug message, sets a global error variable,
 * and assigns `ERR` to the specified return value. Otherwise, it assigns `OK`.
 *
 * @note This macro should be used in functions where pointer validation is required
 *       before performing operations on the pointer. It ensures robust error handling
 *       by setting an error status and providing debugging information.
 *
 * @param[in]  ptr     The pointer to be validated. If `NULL`, an error is logged.
 * @param[out] checking_result  The variable to store the return status (`OK` or `ERR`).
 *
 * @warning Using this macro within control structures (e.g., `if` statements)
 *          without enclosing it in curly braces `{}` may cause unintended behavior
 *          due to its multi-line nature.
 *
 * @attention This macro modifies `checking_result` directly. Ensure `checking_result` is a valid
 *            variable before passing it to the macro.
 *
 * @code
 * // Example usage in a function:
 * int process_data(void *data)
 * {
 *     int status;
 *     GAS_FLOW_REGULATOR_CHECK_PTR(data, status);
 *     if (status == ERR)
 *         return status;
 *
 *     // Proceed with valid data
 *     return OK;
 * }
 * @endcode
 *
 * @see _setGlobalError(), GAS_FLOW_REGULATOR_DEBUG_MSG()
 */
#define GAS_FLOW_REGULATOR_CHECK_PTR(ptr, checking_result)     \
    if (!ptr)                                                  \
    {                                                          \
        GAS_FLOW_REGULATOR_DEBUG_MSG("Detected NULL pointer")  \
        _setGlobalError(ERROR_INVALID_PARAMETER);              \
        checking_result = GAS_FLOW_REGULATOR_ERR;              \
    }                                                          \
    else                                                       \
        checking_result = GAS_FLOW_REGULATOR_OK;

#define GAS_FLOW_REGULATOR_CHECK_PTR_WITH_RETURN(ptr)      \
    do                                                     \
    {                                                      \
        int checking_result = GAS_FLOW_REGULATOR_OK;       \
        GAS_FLOW_REGULATOR_CHECK_PTR(ptr, checking_result) \
        if (checking_result == GAS_FLOW_REGULATOR_ERR)     \
            return checking_result;                        \
    } while (0)

GAS_FLOW_REGULATOR_BEGIN_DECLS

/**
 * @struct Config
 * @brief Structure containing essential parameters for establishing a
 * connection with the gas flow regulator via MODBUS-RTU.
 */
	typedef struct
{
	char* port;   ///< Serial port (e.g., "/dev/ttyUSB0" on Linux or "COM3" on Windows).
	int baudrate; ///< Baud rate for serial communication (e.g., 9600, 19200, 38400).
	int slave_id; ///< MODBUS device ID of the gas regulator (default is often 1).
	int timeout;  ///< Timeout for response (in milliseconds).
} Config;

/**
 * @struct Handle
 * @brief Internal handle that stores the communication context with the gas
 * regulator.
 */
typedef struct
{
	void* modbus_ctx; ///< Pointer to the libmodbus context used for communication.
} Handle;

/**
 * @brief Initializes and establishes a connection to the gas flow regulator.
 *
 * This function sets up a MODBUS-RTU connection over the specified serial port,
 * configures the communication settings, and attempts to connect to the device.
 *
 * @param config Pointer to an `Config` structure containing connection
 * parameters.
 * @param handle Pointer to an `Handle` structure that will be populated
 * upon success.
 * @return Returns `OK` if the connection is successfully established,
 * otherwise an error code.
 */
GAS_FLOW_REGULATOR_API int Init(const Config* GAS_FLOW_REGULATOR_RESTRICT config, Handle* GAS_FLOW_REGULATOR_RESTRICT handle);

/**
 * @brief Sends a new flow rate setpoint to the gas regulator.
 *
 * The setpoint value determines the desired gas flow rate, which the regulator
 * will attempt to maintain. The value is provided in SCCM (Standard Cubic
 * Centimeters per Minute).
 *
 * @param handle Pointer to an initialized `Handle` structure.
 * @param setpoint Desired gas flow rate in SCCM.
 * @return Returns `OK` on success, or an error code if the command fails.
 */
GAS_FLOW_REGULATOR_API int SetFlow(Handle* GAS_FLOW_REGULATOR_RESTRICT handle, float setpoint);

/**
 * @brief Retrieves the current measured gas flow rate.
 *
 * This function queries the gas flow regulator for the real-time flow rate
 * measurement and returns the value in SCCM.
 *
 * @param handle Pointer to an initialized `Handle` structure.
 * @param flow Pointer to a float variable where the retrieved flow value will
 * be stored.
 * @return Returns `OK` on success, or an error code if the request fails.
 */
GAS_FLOW_REGULATOR_API int GetFlow(Handle* GAS_FLOW_REGULATOR_RESTRICT handle, float* GAS_FLOW_REGULATOR_RESTRICT flow);

/**
 * @brief Selects the gas type for the regulator.
 *
 * The regulator supports multiple pre-configured gases. This function allows
 * selecting the active gas calibration profile.
 *
 * @param handle Pointer to an initialized `Handle` structure.
 * @param gas_id Integer representing the gas type (e.g., 7 for Helium).
 * @return Returns `OK` if the gas type is successfully set, otherwise an
 * error code.
 */
GAS_FLOW_REGULATOR_API int SetGas(Handle* GAS_FLOW_REGULATOR_RESTRICT handle, int gas_id);

/**
 * @brief Closes the connection to the gas regulator and frees resources.
 *
 * This function terminates the MODBUS-RTU communication session and releases
 * any allocated memory or handles.
 *
 * @param handle Pointer to an initialized `Handle` structure.
 */
GAS_FLOW_REGULATOR_API void Close(Handle* GAS_FLOW_REGULATOR_RESTRICT handle);

/**
 * @brief Retrieves the description of the last occurred error.
 *
 * This function provides a human-readable description of the last error
 * encountered in the RRG GAS_FLOW_REGULATOR_API. It is useful for debugging and logging purposes.
 *
 * @return A string containing the error message.
 */
GAS_FLOW_REGULATOR_API const char* GasFlowRegulator_GetLastError();

GAS_FLOW_REGULATOR_END_DECLS

#endif // !GAS_FLOW_REGULATOR_H
