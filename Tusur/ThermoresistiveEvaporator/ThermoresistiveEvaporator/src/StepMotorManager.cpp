#include "framework.h"
#include "StepMotorManager.h"
#include "StatusConstants.h"
#include "Constants.h"

StepMotorManager g_StepMotor(sm_constants::kdefault_com_port);

int StepMotorManager::read_holding_register(int addr)
{
	uint16_t readbacks[kreadbacks_size]{};
	if (modbus_read_registers(m_ctx.get(), addr, 1, readbacks) == -1)
		return SM_ERROR_RW_HOLDING_REGISTER;

	return static_cast<int>(readbacks[0]);
}

int StepMotorManager::write_register(int addr, uint16_t val)
{
	if (modbus_write_register(m_ctx.get(), addr, val) == -1)
		return SM_ERROR_RW_HOLDING_REGISTER;

	return STATUS_OK;
}

int StepMotorManager::is_forward_button_pressed() { return read_holding_register(514) == 1; }

int StepMotorManager::is_reverse_button_pressed() { return read_holding_register(515) == 1; }

StepMotorManager::StepMotorManager(const char* port) : m_ctx(nullptr, ModbusDeleter) { connect(port); }

StepMotorManager::~StepMotorManager() {}

int StepMotorManager::connect(const char* port)
{
	// 1. Initializing connection.
	m_ctx.reset(modbus_new_rtu(port, 115200, 'N', 8, 1));
	if (!m_ctx)
		return SM_ERROR_INIT_CONNECTION_FAILED;

	// 2. Setting to slave.
	if (modbus_set_slave(m_ctx.get(), 3) == -1)
		return SM_ERROR_SET_SLAVE_FAILED;

	// 3. Establishing the connection.
	if (modbus_connect(m_ctx.get()) == -1)
	{
		m_ctx.reset();
		return SM_ERROR_CONNECT_FAILED;
	}

	return STATUS_OK;
}

int StepMotorManager::open()
{
	// Writing 1 to 512 and 513 registers.
	if (write_register(512, 1) == SM_ERROR_RW_HOLDING_REGISTER)
		return SM_ERROR_SET_512_REG_TO_1;
	if (write_register(513, 0) == SM_ERROR_RW_HOLDING_REGISTER)
		return SM_ERROR_SET_513_REG_TO_0;

	return STATUS_OK;
}

int StepMotorManager::close()
{
	// Writing 1 to 512 and 513 registers.
	if (write_register(512, 0) == SM_ERROR_RW_HOLDING_REGISTER)
		return SM_ERROR_SET_512_REG_TO_0;
	if (write_register(513, 1) == SM_ERROR_RW_HOLDING_REGISTER)
		return SM_ERROR_SET_513_REG_TO_1;

	return STATUS_OK;
}

int StepMotorManager::stop()
{
	// Writing 1 to 512 and 513 registers.
	if (write_register(512, 0) == SM_ERROR_RW_HOLDING_REGISTER)
		return SM_ERROR_SET_512_REG_TO_0;
	if (write_register(513, 0) == SM_ERROR_RW_HOLDING_REGISTER)
		return SM_ERROR_SET_513_REG_TO_0;

	return STATUS_OK;
}
