using System.Windows.Controls;
using TusurUI.Interfaces;

namespace TusurUI.Source
{
    /**
     * @class PowerSupplyManager
     * @brief Manages the power supply in the application.
     *
     * This class provides functionality to control the power supply, including connecting, turning on,
     * resetting, applying voltage, reading current and voltage, and turning off the power supply.
     */
    public class PowerSupplyManager : IPowerSupplyManager
    {
        private readonly Label _currentValueLabel;
        private readonly Label _voltageValueLabel;

        private bool _IsConnected = false;

        public PowerSupplyManager(Label currentValueLabel, Label voltageValueLabel)
        {
            _currentValueLabel = currentValueLabel ?? throw new ArgumentNullException(nameof(currentValueLabel));
            _voltageValueLabel = voltageValueLabel ?? throw new ArgumentNullException(nameof(voltageValueLabel));
        }

        public void Connect(string comPort)
        {
            PowerSupply.Connect(comPort);
            _IsConnected = true;
        }

        public bool IsConnected() { return _IsConnected; }

        public void TurnOn(string comPort)
        {
            Connect(comPort);
            ExecuteCommand(PowerSupply.TurnOn);
        }

        public void Reset(string comPort)
        {
            Connect(comPort);
            ExecuteCommand(PowerSupply.Reset);
        }

        public void ApplyVoltage(double currentValue, ushort voltageValue)
        {
            ExecuteCommand(() => PowerSupply.SetCurrentVoltage((ushort)currentValue, voltageValue));
        }

        public void ReadCurrentVoltageAndChangeTextBox()
        {
            int current = PowerSupply.ReadCurrent();
            if (current == -1)
                throw new Exception(PowerSupply.GetErrorMessage(current));

            _currentValueLabel.Content = current.ToString();

            int voltage = PowerSupply.ReadVoltage();
            if (voltage == -2)
                throw new Exception(PowerSupply.GetErrorMessage(voltage));

            // Convert the voltage to float by dividing by 100
            float voltageFloat = voltage / 100.0f;
            _voltageValueLabel.Content = voltageFloat.ToString("F2");
        }

        public void TurnOff(string comPort)
        {
            Connect(comPort);
            ExecuteCommand(PowerSupply.TurnOff);
        }

        private void ExecuteCommand(Func<int> command)
        {
            string? err = GetErrorMessage(command());
            if (err != null)
            {
                _IsConnected = false;
                throw new Exception(err);
            }
        }

        private string? GetErrorMessage(int errorCode)
        {
            if (errorCode > 0)
                return PowerSupply.GetErrorMessage(errorCode);
            return null;
        }
    }
}
