#ifdef THERMORESISTIVEEVAPORATOR_EXPORTS
#define POWERSUPPLYMANAGER_API __declspec(dllexport)
#else
#define POWERSUPPLYMANAGER_API __declspec(dllimport)
#endif

#include <memory>
#include <chrono>
#include <thread>
#include <functional>

#include "modbus.h"
#include "Constants.h"

/**
 * @class PowerSupplyManager
 * @brief Manages the power supply via Modbus communication.
 *
 * This class provides methods to connect to a power supply, set current and
 * voltage, read current and voltage values, and control the power supply's
 * operations such as turning on, turning off, and resetting the zero point.
 */
class POWERSUPPLYMANAGER_API PowerSupplyManager
{
private:
	uint16_t buffer[kbuffer_size];                       ///< Buffer for storing Modbus data.
	std::unique_ptr<modbus_t, void(*)(modbus_t*)> m_ctx; ///< Unique pointer to Modbus context with custom deleter.
	int timer_val{};
public:
	/**
	 * @brief Constructor that initializes the power supply manager with a given port.
	 * @param port The serial port to connect to.
	 */
	PowerSupplyManager(const char* port);
	
	/// @brief Dtor.
	~PowerSupplyManager();

	/**
	 * @brief Custom deleter for Modbus context.
	 *		  Closes and frees the Modbus context if it is not null.
	 * @param m Pointer to Modbus context.
	 */
	static void ModbusDeleter(modbus_t* m) {
		if (m) {
			modbus_close(m);
			modbus_free(m);
		}
	}

	/**
	 * @brief Connects to the power supply via the specified port.
	 *
	 * Initializes the Modbus RTU connection, sets the Modbus slave ID,
	 * and establishes the connection.
	 *
	 * @param port The serial port to connect to.
	 * @return int Status code indicating success (STATUS_OK) or specific error.
	 */
	int connect(const char* port);

	/**
	 * @brief Sets the current and voltage for the power supply.
	 *
	 * Writes the specified current and voltage values to the respective
	 * Modbus registers.
	 *
	 * @param current The desired current value.
	 * @param voltage The desired voltage value.
	 * @return int Status code indicating success (STATUS_OK) or specific error.
	 */
	int set_current_voltage(uint16_t current, uint16_t voltage);

	/**
	 * @brief Reads the current value from the power supply.
	 *		  Reads the current value from the Modbus input register.
	 * @return int The current value read from the register, or an error code.
	 */
	int read_current();

	/**
	 * @brief Reads the voltage value from the power supply.
	 * @return int The voltage value read from the register, or an error code.
	 */
	int read_voltage();

	/**
	 * @brief Turns on the power supply.
	 *		  Sends commands to turn on the power supply and set it to work mode.
	 * @return int Status code indicating success (STATUS_OK) or specific error.
	 */
	int turn_on();

	/**
	 * @brief Turns off the power supply.
	 *		  Sends commands to reset the current and voltage, turn off work mode,
	 *		  and then turn off the power supply.
	 * @return int Status code indicating success (STATUS_OK) or specific error.
	 */
	int turn_off();

	/**
	 * @brief Resets "ÇÏ" register of the power supply.
	 *		  Sends a command to reset the "ÇÏ" register of the power supply.
	 * @return int Status code indicating success (STATUS_OK) or specific error.
	 */
	int reset_zp();
	/**
	*@brief Set the timer, i.e. set the value of "timer_val"
	*	Timer is user defined on the HMI
	*	The value will be in minutes
	* @return void function, returns nothing
	*/
	void set_timer(int t) { timer_val = t; }
	/**
	* @brief A funcntion to turn the power supply block and then turn it off using a timer
	*	Timer is defined by the user and is stored as as the timer value "timer_val"
	* @return int Status code indicating success (STATUS_OK) or specific error
	*/
	int turn_on_with_timer();
};

///< Global instance of the extern variable with defaulted value of COM-port.
extern POWERSUPPLYMANAGER_API PowerSupplyManager g_PowerSupply;

extern "C" {
	POWERSUPPLYMANAGER_API int PowerSupply_Connect(const char* port) { return g_PowerSupply.connect(port); }

	POWERSUPPLYMANAGER_API int PowerSupply_SetCurrentVoltage(uint16_t current, uint16_t voltage) { return g_PowerSupply.set_current_voltage(current, voltage); }

	POWERSUPPLYMANAGER_API int PowerSupply_TurnOn() { return g_PowerSupply.turn_on(); }

	POWERSUPPLYMANAGER_API int PowerSupply_TurnOff() { return g_PowerSupply.turn_off(); }

	POWERSUPPLYMANAGER_API int PowerSupply_ReadCurrent() { return g_PowerSupply.read_current(); }

	POWERSUPPLYMANAGER_API int PowerSupply_ReadVoltage() { return g_PowerSupply.read_voltage(); }

	POWERSUPPLYMANAGER_API int PowerSupply_ResetZP() { return g_PowerSupply.reset_zp(); }

	POWERSUPPLYMANAGER_API void PowerSupply_SetTimer(int t) { g_PowerSupply.set_timer(t); }

	POWERSUPPLYMANAGER_API int PowerSupply_TurnOnWithTimer() { return g_PowerSupply.turn_on_with_timer(); }
}
