#ifdef _WIN32
#include "modbus.h"
#else
#include <modbus/modbus.h>
#endif

#include "relay.h"

// Global error variable definition.
int GlobalError = RELAY_OK;

int Init(const Config* RELAY_RESTRICT config, Handle* RELAY_RESTRICT handle)
{
	// 1. Validate input parameters.
	RELAY_CHECK_PTR_WITH_RETURN(config);
	RELAY_CHECK_PTR_WITH_RETURN(handle);

	// 2. Initialize MODBUS-RTU context using default serial configuration.
	modbus_t* ctx = modbus_new_rtu(
		config->port, config->baudrate, RELAY_DEFAULT_PARITY,
		RELAY_DEFAULT_DATA_BITS, RELAY_DEFAULT_STOP_BITS);
	if (!ctx)
	{
		MODBUS_DEBUG_MSG;
		_setGlobalError(RELAY_ERROR_FAILED_CREATE_CONTEXT);
		return RELAY_ERR;
	}

	// 3. Set MODBUS slave ID and check for errors.
	if (modbus_set_slave(ctx, config->slave_id) == MODBUS_ERR)
	{
		MODBUS_DEBUG_MSG;
		modbus_free(ctx);
		_setGlobalError(RELAY_ERROR_FAILED_SET_SLAVE);
		return RELAY_ERR;
	}

	// 4. Configure response timeout and check for errors.
	if (modbus_set_response_timeout(ctx, 0, config->timeout * 1000) == MODBUS_ERR)
	{
		MODBUS_DEBUG_MSG;
		modbus_free(ctx);
		_setGlobalError(RELAY_ERROR_FAILED_SET_TIMEOUT);
		return RELAY_ERR;
	}

	// 5. Attempt to connect to the MODBUS device.
	if (modbus_connect(ctx) == MODBUS_ERR)
	{
		MODBUS_DEBUG_MSG;
		modbus_free(ctx);
		_setGlobalError(RELAY_ERROR_FAILED_CONNECT);
		return RELAY_ERR;
	}

	// 6. Store the context in the handle and check it on NULL.
	handle->modbus_ctx = ctx;
	RELAY_CHECK_PTR_WITH_RETURN(handle->modbus_ctx);

	_resetGlobalError();
	return RELAY_OK;
}

int TurnOn(Handle* RELAY_RESTRICT handle)
{
	// 1. Validate input parameters.
	RELAY_CHECK_PTR_WITH_RETURN(handle);
	RELAY_CHECK_PTR_WITH_RETURN(handle->modbus_ctx);

	// 2. Write 1 to MODBUS register 512.
	if (modbus_write_register(handle->modbus_ctx, MODBUS_REGISTER_TURN_ON_OFF, 1) == MODBUS_ERR)
	{
		MODBUS_DEBUG_MSG;
		_setGlobalError(RELAY_ERROR_FAILED_WRITE_REGISTER);
		return RELAY_ERR;
	}

	// 3. If everything is fine after modbus operation, resetting global error code to 0.
	_resetGlobalError();
	return RELAY_OK;
}

int TurnOff(Handle* RELAY_RESTRICT handle)
{
	// 1. Validate input parameters.
	RELAY_CHECK_PTR_WITH_RETURN(handle);
	RELAY_CHECK_PTR_WITH_RETURN(handle->modbus_ctx);

	// 2. Write 0 to MODBUS register 512.
	if (modbus_write_register(handle->modbus_ctx, MODBUS_REGISTER_TURN_ON_OFF, 0) == MODBUS_ERR)
	{
		MODBUS_DEBUG_MSG;
		_setGlobalError(RELAY_ERROR_FAILED_WRITE_REGISTER);
		return RELAY_ERR;
	}

	// 3. If everything is fine after modbus operation, resetting global error code to 0.
	_resetGlobalError();
	return RELAY_OK;
}

void Close(Handle* RELAY_RESTRICT handle)
{
	if (handle && handle->modbus_ctx)
	{
		modbus_close(handle->modbus_ctx);
		modbus_free(handle->modbus_ctx);
	}
}

const char* Relay_GetLastError()
{
	switch (GlobalError)
	{
	case RELAY_OK:
		return "No error.";
	case RELAY_ERROR_FAILED_CONNECT:
		return "Error: Connection to the MODBUS device failed.";
	case RELAY_ERROR_FAILED_CREATE_CONTEXT:
		return "Error: Failed to create a MODBUS-RTU context.";
	case RELAY_ERROR_FAILED_SET_SLAVE:
		return "Error: Failed to set MODBUS slave ID.";
	case RELAY_ERROR_FAILED_SET_TIMEOUT:
		return "Error: Failed to set MODBUS response timeout.";
	case RELAY_ERROR_FAILED_WRITE_REGISTER:
		return "Error: Failed to write a MODBUS register.";
	case ERROR_INVALID_PARAMETER:
		return "Error: Invalid parameter provided to function.";
	default:
		return "Unknown error occurred.";
	}
}
