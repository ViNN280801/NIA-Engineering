namespace TusurUI.Interfaces
{
    /**
     * @interface IStepMotorManager
     * @brief Interface for managing the step motor in the application.
     *
     * This interface provides methods to control the step motor, including opening, closing,
     * and stopping the shutter, as well as checking the shutter's status.
     */
    public interface IStepMotorManager
    {
        /**
         * @brief Opens the shutter by moving the step motor forward.
         * @param comPort The COM port to which the step motor is connected.
         *
         * This method commands the step motor to move forward, effectively opening the shutter.
         */
        void Forward(string comPort);

        /**
         * @brief Closes the shutter by moving the step motor backward.
         * @param comPort The COM port to which the step motor is connected.
         *
         * This method commands the step motor to move backward, effectively closing the shutter.
         */
        void Reverse(string comPort);

        /**
         * @brief Stops the step motor.
         * @param comPort The COM port to which the step motor is connected.
         *
         * This method commands the step motor to stop its movement.
         */
        void Stop(string comPort);
    }
}
