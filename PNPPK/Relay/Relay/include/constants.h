#ifndef CONSTANTS_H
#define CONSTANTS_H

/**
 * @def RELAY_DEFAULT_PARITY
 * @brief Default parity configuration for MODBUS-RTU communication.
 */
#define RELAY_DEFAULT_PARITY 'N'

/**
 * @def RELAY_DEFAULT_BAUDRATE
 * @brief Default baudrate for the MODBUS-RTU communication for the relay.
 */
#define RELAY_DEFAULT_BAUDRATE 115200

/**
 * @def RELAY_DEFAULT_SLAVE_ID
 * @brief Default slave ID for the MODBUS-RTU communication for the relay.
 */
#define RELAY_DEFAULT_SLAVE_ID 6

/**
 * @def RELAY_DEFAULT_DATA_BITS
 * @brief Default number of data bits for MODBUS-RTU communication.
 */
#define RELAY_DEFAULT_DATA_BITS 8

/**
 * @def RELAY_DEFAULT_STOP_BITS
 * @brief Default number of stop bits for MODBUS-RTU communication.
 */
#define RELAY_DEFAULT_STOP_BITS 1

/**
 * @def RELAY_DEFAULT_TIMEOUT_MS
 * @brief Default timeout in milliseconds for MODBUS-RTU communication.
 */
#define RELAY_DEFAULT_TIMEOUT_MS 10

/**
 * @def MODBUS_REGISTER_TURN_ON
 * @brief MODBUS register for turning on/off the relay. If write 1 - turn on, if 0 - turn off.
 */
#define MODBUS_REGISTER_TURN_ON_OFF 512

#endif // !CONSTANTS_H
