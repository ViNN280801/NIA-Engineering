#include <cstring>

#include "framework.h"
#include "PowerSupplyManager.h"
#include "StatusConstants.h"

PowerSupplyManager g_PowerSupply(ps_constants::kdefault_com_port);

PowerSupplyManager::PowerSupplyManager(const char* port) : m_ctx(nullptr, ModbusDeleter)
{
	std::memset(buffer, 0, 20ul);
	connect(port);
}

PowerSupplyManager::~PowerSupplyManager() {}

int PowerSupplyManager::connect(const char* port)
{
	// 1. Initializing connection.
	m_ctx.reset(modbus_new_rtu(port, 19200, 'N', 8, 1));
	if (!m_ctx)
		return PS_ERROR_INIT_CONNECTION_FAILED;

	// 2. Setting to slave.
	if (modbus_set_slave(m_ctx.get(), 1) == -1)
		return PS_ERROR_SET_SLAVE_FAILED;

	// 3. Establishing the connection.
	if (modbus_connect(m_ctx.get()) == -1)
	{
		m_ctx.reset();
		return PS_ERROR_CONNECT_FAILED;
	}

	return STATUS_OK;
}

int PowerSupplyManager::set_current_voltage(uint16_t current, uint16_t voltage)
{
	// 1. Setting up the current register.
	if (modbus_write_register(m_ctx.get(), 18, current) == -1)
		return PS_ERROR_SET_CURRENT_FAILED;

	// 2. Setting up the voltage register.
	if (modbus_write_register(m_ctx.get(), 19, voltage * kvoltage_multiplier) == -1)
		return PS_ERROR_SET_VOLTAGE_FAILED;

	return STATUS_OK;
}

int PowerSupplyManager::read_current()
{
	// Reading input registers from 0x20 addr.
	if (modbus_read_input_registers(m_ctx.get(), 20, 1, buffer) == -1)
		return PS_ERROR_READ_CURRENT;

	return static_cast<int>(buffer[0]);
}

int PowerSupplyManager::read_voltage()
{
	// Reading input registers from 0x21 addr.
	if (modbus_read_input_registers(m_ctx.get(), 21, 1, buffer) == -1)
		return PS_ERROR_READ_VOLTAGE;

	return static_cast<int>(buffer[0]);
}

int PowerSupplyManager::turn_on()
{
	// 1. Turning on power supply.
	if (modbus_write_bit(m_ctx.get(), 272, 1) == -1)
		return PS_ERROR_POWER_SUPPLY_TURN_ON_FAILED;

	// 2. Turning on workmode of the power supply.
	if (modbus_write_bit(m_ctx.get(), 273, 1) == -1)
		return PS_ERROR_POWER_SUPPLY_TURN_ON_WORKMODE_FAILED;

	return STATUS_OK;
}

int PowerSupplyManager::turn_off()
{
	// 1. Resetting current.
	if (modbus_write_register(m_ctx.get(), 18, 0) == -1)
		return PS_ERROR_RESET_CURRENT;

	// 2. Resetting voltage.
	if (modbus_write_register(m_ctx.get(), 19, 0) == -1)
		return PS_ERROR_RESET_VOLTAGE;

	// 3. Resetting workmode.
	if (modbus_write_bit(m_ctx.get(), 273, 0) == -1)
		return PS_ERROR_RESET_WORKMODE;

	// 4. Turning of the power supply.
	if (modbus_write_bit(m_ctx.get(), 272, 0) == -1)
		return PS_ERROR_POWER_SUPPLY_TURN_OFF_FAILED;

	return STATUS_OK;
}

int PowerSupplyManager::reset_zp()
{
	if (modbus_write_register(m_ctx.get(), 36, 0) == -1)
		return PS_ERROR_RESET_ZP_FAILED;

	return STATUS_OK;
}

int PowerSupplyManager::turn_on_with_timer()
{
	// 1. If "timer_val" is negative
	if (timer_val < 0) {
		return PS_ERROR_UNSUPPORTED_TIMER_VALUE;
	}
	// 2. If timer value is 0, then it the usual "turn_on" will be executed
	else if (timer_val == 0)
		return PowerSupplyManager::turn_on();
	// 3. The timer value is positive, so timer operation will start
	else {
		// 4. The power supply will turn on

		if (not(PowerSupplyManager::turn_on()))
			return PS_ERROR_POWER_SUPPLY_TURN_ON_FAILED;

		// 5. Now the operation will be paused for user specified amount of time (minutes)

		std::this_thread::sleep_for(std::chrono::minutes(timer_val));
	}
	// 6. Power supply has to be turned off after user specified amount of minutes
	return PowerSupplyManager::turn_off();
}
