namespace TusurUI.Interfaces
{
    /**
     * @interface IPowerSupplyTimerManager
     * @brief Interface for managing the power supply timer.
     *
     * This interface defines methods for starting and resetting the countdown timer for the power supply.
     */
    public interface IPowerSupplyTimerManager
    {
        /**
         * @brief Starts the countdown timer.
         *
         * This method initializes and starts the countdown timer based on the value provided in the associated TextBox.
         */
        void StartCountdown(bool isCountdown);

        /**
         * @brief Resets the countdown timer.
         *
         * This method stops the countdown timer and resets the associated TextBox to its initial state.
         */
        void ResetTimer();
    }
}
