namespace TusurUI.Interfaces
{
    /**
     * @interface IBaseTimerManager
     * @brief Interface for managing a timer that executes a specific action at regular intervals.
     *
     * This interface provides methods to start and stop a timer, which executes a predefined action at specified intervals.
     */
    public interface IBaseTimerManager
    {
        /**
         * @brief Starts the timer.
         *
         * This method starts the timer, which will execute a predefined action at regular intervals.
         */
        void Start();

        /**
         * @brief Stops the timer.
         *
         * This method stops the timer, preventing it from executing any further actions.
         */
        void Stop();
    }
}
