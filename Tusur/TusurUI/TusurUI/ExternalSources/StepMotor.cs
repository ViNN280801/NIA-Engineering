using System.Runtime.InteropServices;

namespace TusurUI.ExternalSources
{
    public class StepMotor
    {
        [DllImport("Libs/ThermoresistiveEvaporator.dll", CallingConvention = CallingConvention.Cdecl, CharSet = CharSet.Ansi)]
        private static extern int StepMotor_Connect(string port);

        [DllImport("Libs/ThermoresistiveEvaporator.dll", CallingConvention = CallingConvention.Cdecl)]
        private static extern int StepMotor_Forward();

        [DllImport("Libs/ThermoresistiveEvaporator.dll", CallingConvention = CallingConvention.Cdecl)]
        private static extern int StepMotor_Reverse();

        [DllImport("Libs/ThermoresistiveEvaporator.dll", CallingConvention = CallingConvention.Cdecl)]
        private static extern int StepMotor_Stop();

        [DllImport("Libs/ThermoresistiveEvaporator.dll", CallingConvention = CallingConvention.Cdecl)]
        private static extern int StepMotor_GetLastState();

        [DllImport("Libs/ThermoresistiveEvaporator.dll", CallingConvention = CallingConvention.Cdecl)]
        private static extern int StepMotor_IsForwardButtonPressed();

        [DllImport("Libs/ThermoresistiveEvaporator.dll", CallingConvention = CallingConvention.Cdecl)]
        private static extern int StepMotor_IsReverseButtonPressed();

        public StepMotor() { }

        public static int Connect(string port) { return StepMotor_Connect(port); }

        public static int Forward() { return StepMotor_Forward(); }

        public static int Reverse() { return StepMotor_Reverse(); }

        public static int Stop() { return StepMotor_Stop(); }

        public static int GetLastMotorState() { return StepMotor_GetLastState(); }

        public static bool IsForwardButtonPressed() { return StepMotor_IsForwardButtonPressed() == 1; }

        public static bool IsReverseButtonPressed() { return StepMotor_IsReverseButtonPressed() == 1; }

        private void UpdateMotorStateDisplay()
        {
            int state = StepMotor_GetLastState();
            switch (state)
            {
                case 0: // IDLE
                    break;
                case 1: // FORWARD
                    break;
                case 2: // REVERSE
                    break;
                default:
                    break;
            }
        }


        private static string GetErrorMessageEN(int errorCode)
        {
            return errorCode switch
            {
                0 => "Operation successful.",
                1 => "Failed to initialize connection.",
                2 => "Failed to set device as slave.",
                3 => "Failed to connect to the device.",
                4 => "The stepper motor could not be started in FORWARD mode (set the value of 512 register to 1).",
                5 => "The stepper motor could not be started in REVERSE mode (set the value of 513 registers to 1).",
                6 => "It was not possible to reset the FORWARD mode of the stepper motor (set the value of 512 register to 0).",
                7 => "It was not possible to reset the REVERSE mode of the stepper motor (set the value of register 513 to 0).",
                8 => "Shutter already closed.",
                _ => "Unknown error."
            };
        }

        private static string GetErrorMessageRU(int errorCode)
        {
            return errorCode switch
            {
                0 => "Операция прошла успешно.",
                1 => "Не удалось инициализировать соединение.",
                2 => "Не удалось установить устройство как slave.",
                3 => "Не удалось подключиться к устройству.",
                4 => "Не удалось запустить шаговый двигатель в режиме FORWARD (установить значение 512 регистра в 1).",
                5 => "Не удалось запустить шаговый двигатель в режиме REVERSE (установить значение 513 регистра в 1).",
                6 => "Не удалось произвести сброс режима FORWARD у шагового двигателя (установить значение 512 регистра в 0).",
                7 => "Не удалось произвести сброс режима REVERSE у шагового двигателя (установить значение 513 регистра в 0).",
                8 => "Заслонка уже закрыта.",
                _ => "Неизвестная ошибка."
            };
        }

        public static string GetErrorMessage(int errorCode, string language = "RU")
        {
            string message = language switch
            {
                "RU" => GetErrorMessageRU(errorCode),
                "EN" => GetErrorMessageEN(errorCode),
                _ => "Language not supported."
            };

            return language == "RU" ? $"StepMotor.dll: Код ошибки: {errorCode}. Сообщение: {message}"
                : $"StepMotor.dll:Error code: {errorCode}. Message: {message}";
        }
    }
}
