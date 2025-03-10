#ifdef THERMORESISTIVEEVAPORATOR_EXPORTS
#define STEPMOTORMANAGER_API __declspec(dllexport)
#else
#define STEPMOTORMANAGER_API __declspec(dllimport)
#endif

#include <memory>

#include "modbus.h"
#include "modbus_dev.h"

/**
 * @class StepMotorManager
 * @brief Manages the step motor via Modbus communication.
 *
 * This class provides methods to connect to a step motor, read and write
 * registers, and control the step motor's operations such as opening, closing,
 * and stopping the motor.
 */
class STEPMOTORMANAGER_API StepMotorManager : public modbus_dev
{
private:
	std::unique_ptr<modbus_t, void(*)(modbus_t*)> m_ctx; ///< Unique pointer to Modbus context with custom deleter.

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
	 * @brief Reads a holding register from the step motor.
	 * @param addr The address of the holding register to read.
	 * @return int The value of the register, or an error code.
	 */
	int read_holding_register(int addr);

	/**
	 * @brief Writes a value to a register of the step motor.
	 * @param addr The address of the register to write to.
	 * @param val The value to write to the register.
	 * @return int Status code indicating success (STATUS_OK) or specific error.
	 */
	int write_register(int addr, uint16_t val);

public:
	/**
	 * @brief Constructor that initializes the step motor manager with a given port.
	 * @param port The serial port to connect to.
	 */
	StepMotorManager(const char* port);

	/// @brief Dtor.
	~StepMotorManager();

	/**
	 * @brief Connects to the step motor via the specified port.
	 *
	 * Initializes the Modbus RTU connection, sets the Modbus slave ID,
	 * and establishes the connection.
	 *
	 * @param port The serial port to connect to.
	 * @return int Status code indicating success (STATUS_OK) or specific error.
	 */
	int connect(const char* port);

	/**
	 * @brief Opens the step motor.
	 *		  Writes to the necessary registers to open the step motor.
	 * @return int Status code indicating success (STATUS_OK) or specific error.
	 */
	int open();

	/**
	 * @brief Closes the step motor.
	 *		  Writes to the necessary registers to close the step motor.
	 * @return int Status code indicating success (STATUS_OK) or specific error.
	 */
	int close();

	/**
	 * @brief Stops the step motor.
	 *		  Writes to the necessary registers to stop the step motor.
	 * @return int Status code indicating success (STATUS_OK) or specific error.
	 */
	int stop();

	/**
	 * @brief Checks if the forward button is pressed.
	 *
	 * Reads the holding register associated with the forward button and
	 * checks if it is pressed.
	 *
	 * @return int 1 if the forward button is pressed, 0 otherwise.
	 */
	int is_forward_button_pressed();

	/**
	 * @brief Checks if the reverse button is pressed.
	 *
	 * Reads the holding register associated with the reverse button and
	 * checks if it is pressed.
	 *
	 * @return int 1 if the reverse button is pressed, 0 otherwise.
	 */
	int is_reverse_button_pressed();
};

///< Global instance of the extern variable with defaulted value of COM-port.
extern STEPMOTORMANAGER_API StepMotorManager g_StepMotor;

extern "C" {
	STEPMOTORMANAGER_API int StepMotor_Connect(const char* port) { return g_StepMotor.connect(port); }

	STEPMOTORMANAGER_API int StepMotor_Forward() { return g_StepMotor.open(); }

	STEPMOTORMANAGER_API int StepMotor_Reverse() { return g_StepMotor.close(); }

	STEPMOTORMANAGER_API int StepMotor_Stop() { return g_StepMotor.stop(); }

	STEPMOTORMANAGER_API int StepMotor_IsForwardButtonPressed() { return g_StepMotor.is_forward_button_pressed(); }

	STEPMOTORMANAGER_API int StepMotor_IsReverseButtonPressed() { return g_StepMotor.is_reverse_button_pressed(); }
}
