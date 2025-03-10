namespace TusurUI.Interfaces
{
    /**
     * @interface IPowerSupplyManager
     * @brief Interface for managing the power supply in the application.
     *
     * This interface provides methods to control the power supply, including connecting, turning on,
     * resetting, applying voltage, reading current and voltage, and turning off the power supply.
     */
    public interface IPowerSupplyManager
    {
        /**
         * @brief Connects to the power supply using the specified COM port.
         * @param comPort The COM port to which the power supply is connected.
         *
         * This method establishes a connection to the power supply using the given COM port.
         */
        void Connect(string comPort);

        /**
         * @brief Turns on the power supply.
         * @param comPort The COM port to which the power supply is connected.
         *
         * This method turns on the power supply using the specified COM port.
         */
        void TurnOn(string comPort);

        /**
         * @brief Resets the power supply.
         * @param comPort The COM port to which the power supply is connected.
         *
         * This method resets the power supply using the specified COM port.
         */
        void Reset(string comPort);

        /**
         * @brief Applies the specified voltage to the power supply.
         * @param currentValue The current value to be set.
         * @param voltageValue The voltage value to be set.
         *
         * This method sets the current and voltage values for the power supply.
         */
        void ApplyVoltage(double currentValue, ushort voltageValue);

        /**
         * @brief Reads the current and voltage values from the power supply and updates the UI.
         *
         * This method reads the current and voltage values from the power supply and updates
         * the corresponding UI elements with these values.
         */
        void ReadCurrentVoltageAndChangeTextBox();

        /**
         * @brief Turns off the power supply.
         * @param comPort The COM port to which the power supply is connected.
         *
         * This method turns off the power supply using the specified COM port.
         */
        void TurnOff(string comPort);
    }
}
