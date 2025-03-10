using TusurUI.ExternalSources;
using TusurUI.Helpers;
using TusurUI.Interfaces;

namespace TusurUI.Source
{
    /**
     * @class StepMotorManager
     * @brief Manages the step motor in the application.
     *
     * This class provides functionality to control the step motor, including opening, closing,
     * and stopping the shutter, as well as checking the shutter's status.
     */
    public class StepMotorManager : IStepMotorManager
    {
        private readonly UIHelper _uiHelper;

        private bool _IsStepMotorConnected = false;

        public StepMotorManager(UIHelper uiHelper)
        {
            _uiHelper = uiHelper ?? throw new ArgumentNullException(nameof(uiHelper));
        }

        public void Forward(string comPort)
        {
            Connect(comPort);
            ExecuteCommand(StepMotor.Forward);
            _uiHelper.SetShutterImageToOpened();
        }

        public void Reverse(string comPort)
        {
            Connect(comPort);
            ExecuteCommand(StepMotor.Reverse);
            _uiHelper.SetShutterImageToClosed();
        }

        public void Stop(string comPort)
        {
            Connect(comPort);
            ExecuteCommand(StepMotor.Stop);
        }

        public bool IsConnected() { return _IsStepMotorConnected; }

        public bool IsShutterOpened()
        {
            return ComponentManager.GetIndicatorImage(_uiHelper.Vaporizer)?.UriSource.ToString().Contains("откр") ?? false;
        }

        public bool IsShutterClosed()
        {
            return ComponentManager.GetIndicatorImage(_uiHelper.Vaporizer)?.UriSource.ToString().Contains("закр") ?? false;
        }

        private void ExecuteCommand(Func<int> command)
        {
            string? err = GetErrorMessage(command());
            if (err != null)
            {
                _IsStepMotorConnected = false;
                throw new Exception(err);
            }
        }

        private string? GetErrorMessage(int errorCode)
        {
            if (errorCode > 0)
                return StepMotor.GetErrorMessage(errorCode);
            return null;
        }

        private void Connect(string comPort)
        {
            StepMotor.Connect(comPort);
            _IsStepMotorConnected = true;
        }
    }
}
