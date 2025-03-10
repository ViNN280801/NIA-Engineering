#pragma once

namespace PowerSupply_constants
{
	static const char* kdefault_com_port{ "COM1" };          ///< Default value of the COM-port.
	static constexpr const short kbuffer_size{ 20 };         ///< Buffer size to read inputs into.
	static constexpr const short kvoltage_multiplier{ 100 }; ///< Needs because register gets values from 0 to 600. Supposed that value 100 equals to 1 V.
}

namespace StepMotor_constants
{
	static constexpr const short kreadbacks_size{ 100 };	  ///< Default size of the readbacks buffer.
	static constexpr const char* kdefault_com_port{ "COM2" }; ///< Default COM-port.
}

namespace ps_constants = PowerSupply_constants;
namespace sm_constants = StepMotor_constants;

using namespace PowerSupply_constants;
using namespace StepMotor_constants;
