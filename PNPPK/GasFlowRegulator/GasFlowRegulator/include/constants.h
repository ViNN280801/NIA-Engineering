#ifndef CONSTANTS_H
#define CONSTANTS_H

/**
 * @def GAS_FLOW_REGULATOR_DEFAULT_PARITY
 * @brief GAS_FLOW_REGULATOR_DEFAULT parity configuration for MODBUS-RTU communication.
 */
#define GAS_FLOW_REGULATOR_DEFAULT_PARITY 'N'

/**
 * @def GAS_FLOW_REGULATOR_DEFAULT_BAUDRATE
 * @brief GAS_FLOW_REGULATOR_DEFAULT baudrate for the MODBUS-RTU communication for the RRG.
 */
#define GAS_FLOW_REGULATOR_DEFAULT_BAUDRATE 38400

/**
 * @def GAS_FLOW_REGULATOR_DEFAULT_SLAVE_ID
 * @brief GAS_FLOW_REGULATOR_DEFAULT slave ID for the MODBUS-RTU communication for the RRG.
 */
#define GAS_FLOW_REGULATOR_DEFAULT_SLAVE_ID 1

/**
 * @def GAS_FLOW_REGULATOR_DEFAULT_DATA_BITS
 * @brief GAS_FLOW_REGULATOR_DEFAULT number of data bits for MODBUS-RTU communication.
 */
#define GAS_FLOW_REGULATOR_DEFAULT_DATA_BITS 8

/**
 * @def GAS_FLOW_REGULATOR_DEFAULT_STOP_BITS
 * @brief GAS_FLOW_REGULATOR_DEFAULT number of stop bits for MODBUS-RTU communication.
 */
#define GAS_FLOW_REGULATOR_DEFAULT_STOP_BITS 1

/**
 * @def GAS_FLOW_REGULATOR_DEFAULT_TIMEOUT_MS
 * @brief GAS_FLOW_REGULATOR_DEFAULT timeout in milliseconds for MODBUS-RTU communication.
 */
#define GAS_FLOW_REGULATOR_DEFAULT_TIMEOUT_MS 50

/**
 * @def MODBUS_REGISTER_SETPOINT
 * @brief MODBUS register for setting the flow setpoint (2053-2054).
 */
#define MODBUS_REGISTER_SETPOINT 2053

/**
 * @def MODBUS_REGISTER_FLOW
 * @brief MODBUS register for reading the current flow (2103).
 */
#define MODBUS_REGISTER_FLOW 2103

/**
 * @def MODBUS_REGISTER_GAS
 * @brief MODBUS register for setting the gas type (2100).
 */
#define MODBUS_REGISTER_GAS 2100

#endif // !CONSTANTS_H
