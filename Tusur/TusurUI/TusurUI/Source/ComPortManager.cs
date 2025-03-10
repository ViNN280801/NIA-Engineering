using System.IO.Ports;
using System.Windows.Controls;
using TusurUI.Interfaces;
using TusurUI.Errors;

namespace TusurUI.Source
{
    /**
     * @class ComPortManager
     * @brief Manages the COM ports in the application.
     *
     * This class provides functionality to populate a ComboBox with available COM ports,
     * check the validity of the selected COM port, and retrieve the name of the selected COM port.
     */
    public class ComPortManager : IComPortManager
    {
        private readonly ComboBox _comboBox;
        private bool _isPopulatingComboBoxes = false;

        public ComPortManager(ComboBox comboBox)
        {
            _comboBox = comboBox ?? throw new ArgumentNullException(nameof(comboBox));
        }

        public void PopulateComPortComboBox(ComboBox otherComboBox)
        {
            if (_isPopulatingComboBoxes)
                return;

            _isPopulatingComboBoxes = true;

            try
            {
                string[] ports = SerialPort.GetPortNames();

                // Exclude the port selected in the other ComboBox
                var availablePorts = ports.Except(new[] { otherComboBox.SelectedItem?.ToString() }).ToArray();
                _comboBox.ItemsSource = availablePorts;

                if (availablePorts.Length > 0)
                {
                    _comboBox.IsEnabled = true;
                }
                else
                {
                    _comboBox.IsEnabled = true; // Always enabled, no blocking
                }
            }
            finally
            {
                _isPopulatingComboBoxes = false;
            }
        }
        public bool CheckComPort()
        {
            if (IsComPortNotSelected())
            {
                string errorMessage = ErrorMessages.Compose(ErrorMessages.GetErrorMessage("InternalError"), ErrorMessages.GetErrorMessage("EmptyCOM"));
                throw new ArgumentNullException(errorMessage);
            }
            return true;
        }

        public bool IsComPortSelected() { return (_comboBox.SelectedItem != null); }
        public bool IsComPortNotSelected() { return (_comboBox.SelectedItem == null); }

        public string GetComPortName()
        {
            if (_comboBox.SelectedItem == null)
            {
                string errorMessage = ErrorMessages.Compose(ErrorMessages.GetErrorMessage("InternalError"), ErrorMessages.GetErrorMessage("EmptyCOM"));
                throw new ArgumentNullException(errorMessage);
            }

            string? comPort = _comboBox.SelectedItem.ToString();
            if (comPort == null)
            {
                string errorMessage = ErrorMessages.Compose(ErrorMessages.GetErrorMessage("InternalError"), ErrorMessages.GetErrorMessage("EmptyCOM"));
                throw new ArgumentNullException(errorMessage);
            }

            return comPort;
        }
    }
}
