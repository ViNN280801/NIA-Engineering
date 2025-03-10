using System.Windows;
using System.Windows.Controls;
using TusurUI.Source;
using TusurUI.Helpers;
using TusurUI.Errors;
using TusurUI.Logs;
using System.Windows.Media;
using System.IO.Ports;

namespace TusurUI
{
    public partial class MainWindow : Window
    {
        private const int k_InvalidComboBoxItem = -1;
        private const int k_InvalidTime = 0;
        private const int k_MinCurrentValue = 0;
        private const int k_MaxCurrentValue = 200;
        private const int k_UpdateCurrentVoltageIntervalMilliseconds = 100;

        private readonly CurrentVoltageUpdateTimerManager _currentVoltageUpdateTimerManager;
        private readonly ComPortManager _powerSupplyComPortManager;
        private readonly ComPortManager _stepMotorComPortManager;
        public readonly PowerSupplyManager _powerSupplyManager;
        private readonly StepMotorManager _stepMotorManager;
        private readonly UIHelper _uiHelper;

        private ScenariosWindow? _scenariosWindow;

        public MainWindow()
        {
            InitializeComponent();

            _uiHelper = new UIHelper(Vaporizer, SystemStateLabel, VaporizerButtonBase, VaporizerButtonInside, Indicator, CurrentValueLabel, VoltageValueLabel);
            _currentVoltageUpdateTimerManager = new CurrentVoltageUpdateTimerManager(PowerSupplyUpdateCurrentVoltage, k_UpdateCurrentVoltageIntervalMilliseconds);
            _powerSupplyComPortManager = new ComPortManager(PowerSupplyComPortComboBox);
            _stepMotorComPortManager = new ComPortManager(ShutterComPortComboBox);
            _powerSupplyManager = new PowerSupplyManager(CurrentValueLabel, VoltageValueLabel);
            _stepMotorManager = new StepMotorManager(_uiHelper);

            PowerSupplyComPortComboBox.SelectionChanged += ComboBox_SelectionChanged;
            ShutterComPortComboBox.SelectionChanged += ComboBox_SelectionChanged;

            // If shutter opened when program started - change icon.
            if (_stepMotorManager.IsShutterOpened())
                _uiHelper.SetShutterImageToOpened();
            else
                _uiHelper.SetShutterImageToClosed();
        }

        private string? GetLanguage()
        {
            if (LanguageComboBox.SelectedItem != null)
            {
                string selectedLanguage = (LanguageComboBox.SelectedItem as ComboBoxItem)?.Content.ToString() ?? string.Empty;
                if (selectedLanguage == "Русский" || selectedLanguage == "Russian")
                {
                    return "ru";
                }
                else if (selectedLanguage == "Английский" || selectedLanguage == "English")
                {
                    return "en";
                }
            }
            return null;
        }

        private void LanguageComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (LanguageComboBox.SelectedItem != null)
            {
                string selectedLanguage = (LanguageComboBox.SelectedItem as ComboBoxItem)?.Content.ToString() ?? string.Empty;
                if (selectedLanguage == "Русский" || selectedLanguage == "Russian")
                {
                    SetLanguage("ru");
                }
                else if (selectedLanguage == "Английский" || selectedLanguage == "English")
                {
                    SetLanguage("en");
                }

                // Translating dynamic label
                if (SystemStateLabel != null)
                {
                    var foregroundBrush = SystemStateLabel.Foreground as SolidColorBrush;
                    if (foregroundBrush != null)
                    {
                        if (foregroundBrush.Color == Colors.Red)
                        {
                            SystemStateLabel.Content = ErrorMessages.GetErrorMessage("SystemNotWorkingLabel");
                        }
                        else if (foregroundBrush.Color == Colors.Green)
                        {
                            SystemStateLabel.Content = ErrorMessages.GetErrorMessage("SystemWorkingLabel");
                        }
                    }
                }
            }
        }

        private void SetLanguage(string language)
        {
            var mainWindowDictionary = new ResourceDictionary();
            var scenarioWindowDictionary = new ResourceDictionary();
            var stylesDictionary = new ResourceDictionary { Source = new Uri("Styles.xaml", UriKind.Relative) };

            switch (language)
            {
                case "ru":
                    mainWindowDictionary.Source = new Uri("Resources/MainWindowUIElements.ru.xaml", UriKind.Relative);
                    scenarioWindowDictionary.Source = new Uri("Resources/ScenarioWindowUIElements.ru.xaml", UriKind.Relative);
                    ErrorMessages.SetLanguage("ru");
                    LogMessages.SetLanguage("ru");
                    break;
                case "en":
                default:
                    mainWindowDictionary.Source = new Uri("Resources/MainWindowUIElements.en.xaml", UriKind.Relative);
                    scenarioWindowDictionary.Source = new Uri("Resources/ScenarioWindowUIElements.en.xaml", UriKind.Relative);
                    ErrorMessages.SetLanguage("en");
                    LogMessages.SetLanguage("en");
                    break;
            }

            Application.Current.Resources.MergedDictionaries.Clear();
            Application.Current.Resources.MergedDictionaries.Add(stylesDictionary);
            Application.Current.Resources.MergedDictionaries.Add(mainWindowDictionary);
            Application.Current.Resources.MergedDictionaries.Add(scenarioWindowDictionary);

            _scenariosWindow?.TranslateUI();
        }

        private void UpdateComPorts()
        {
            try
            {
                string[] ports = SerialPort.GetPortNames();

                if (ports.Length > 0)
                {
                    // Populate both ComboBoxes with available COM ports
                    _powerSupplyComPortManager.PopulateComPortComboBox(ShutterComPortComboBox);
                    _stepMotorComPortManager.PopulateComPortComboBox(PowerSupplyComPortComboBox);

                    string successMessage = GetLanguage() == "en"
                        ? $"COM ports found: {string.Join(", ", ports)}"
                        : $"Найдены COM-порты: {string.Join(", ", ports)}";
                    ShowSuccess(successMessage);
                }
                else
                {
                    // No COM ports found, disable both ComboBoxes
                    string warningMessage = GetLanguage() == "en"
                        ? "No COM-ports were found."
                        : "Не было найдено ни одного COM-порта.";
                    ShowWarning(warningMessage);

                    PowerSupplyComPortComboBox.IsEnabled = false;
                    ShutterComPortComboBox.IsEnabled = false;
                }
            }
            catch (Exception)
            {
                // Handle errors during COM port scanning
                string errorMessage = GetLanguage() == "en"
                    ? "It was not possible to scan COM ports at the startup stage, try to do it through the \"Scan COM-ports\" button"
                    : "Не удалось просканировать COM-порты на этапе запуска, попробуйте сделать это через кнопку \"Сканировать COM-порты\"";
                ShowError(errorMessage);
            }
        }

        private void PowerSupplyUpdateCurrentVoltage()
        {
            ExecuteWithErrorHandling(() =>
            {
                _powerSupplyManager.ReadCurrentVoltageAndChangeTextBox();
            });
        }

        public bool AreComPortsValid()
        {
            try
            {
                _powerSupplyComPortManager.CheckComPort();
            }
            catch (ArgumentException ex)
            {
                _scenariosWindow?.StopProgram(ex);
                ShowError(ErrorMessages.GetErrorMessage("PowerSupplyComPortError"));
                return false;
            }

            try
            {
                _stepMotorComPortManager.CheckComPort();
            }
            catch (ArgumentException ex)
            {
                _scenariosWindow?.StopProgram(ex);
                ShowError(ErrorMessages.GetErrorMessage("StepMotorComPortError"));
                return false;
            }

            return true;
        }

        protected override void OnClosed(EventArgs e)
        {
            base.OnClosed(e);
            _currentVoltageUpdateTimerManager.Stop();
        }

        private bool IsValidInput(string text)
        {
            foreach (var c in text)
                if (!char.IsDigit(c) && c != ',' && c != '.')
                    return false;
            return true;
        }

        private void ComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (sender == PowerSupplyComPortComboBox)
            {
                // If the selected port in PowerSupplyComboBox is the same as in ShutterComPortComboBox, clear ShutterComPortComboBox selection
                if (PowerSupplyComPortComboBox.SelectedItem != null &&
                    PowerSupplyComPortComboBox.SelectedItem.ToString() == ShutterComPortComboBox.SelectedItem?.ToString())
                {
                    ShutterComPortComboBox.SelectedIndex = -1; // Clear the selection in ShutterComPortComboBox
                }
            }
            else if (sender == ShutterComPortComboBox)
            {
                // If the selected port in ShutterComPortComboBox is the same as in PowerSupplyComPortComboBox, clear PowerSupplyComPortComboBox selection
                if (ShutterComPortComboBox.SelectedItem != null &&
                    ShutterComPortComboBox.SelectedItem.ToString() == PowerSupplyComPortComboBox.SelectedItem?.ToString())
                {
                    PowerSupplyComPortComboBox.SelectedIndex = -1; // Clear the selection in PowerSupplyComPortComboBox
                }
            }
        }

        private void UpdateAvailablePorts(ComboBox comboBoxToUpdate, string portToExclude)
        {
            string[] ports = SerialPort.GetPortNames();

            // Exclude the selected port from the other ComboBox
            var availablePorts = ports.Except(new[] { portToExclude }).ToArray();

            comboBoxToUpdate.SelectionChanged -= ComboBox_SelectionChanged; // Temporarily disable event handler
            comboBoxToUpdate.ItemsSource = availablePorts;

            // If the currently selected port is no longer available, clear the selection
            if (!availablePorts.Contains(comboBoxToUpdate.SelectedItem?.ToString()))
            {
                comboBoxToUpdate.SelectedIndex = -1;
            }

            comboBoxToUpdate.SelectionChanged += ComboBox_SelectionChanged; // Re-enable event handler
        }

        private void OpenShutter()
        {
            ExecuteWithErrorHandling(() =>
            {
                string comPort = _stepMotorComPortManager.GetComPortName();
                _stepMotorManager.Forward(comPort);
                SetShutterImageToOpened();
                ColorizeOpenShutterButton();
            }, () =>
            {
                SetShutterImageToClosed();
                ColorizeCloseShutterButton();
            });
        }

        private void CloseShutter()
        {
            ExecuteWithErrorHandling(() =>
            {
                string comPort = _stepMotorComPortManager.GetComPortName();
                _stepMotorManager.Reverse(comPort);
                SetShutterImageToClosed();
                ColorizeCloseShutterButton();
            }, SetShutterImageToClosed);
        }

        private void StopStepMotor()
        {
            ExecuteWithErrorHandling(() =>
            {
                string comPort = _stepMotorComPortManager.GetComPortName();
                _stepMotorManager.Stop(comPort);
                ColorizeStopStepMotorButton();
            });
        }

        public void ShowWarning(string message, string? title = null)
        {
            string warningTitle = title ?? ErrorMessages.GetErrorMessage("WarningTitle");
            MessageBox.Show(message, warningTitle, MessageBoxButton.OK, MessageBoxImage.Warning);
        }

        public void ShowError(string message, string? title = null)
        {
            string errorTitle = title ?? ErrorMessages.GetErrorMessage("ErrorTitle");
            MessageBox.Show(message, errorTitle, MessageBoxButton.OK, MessageBoxImage.Error);
        }

        public void ShowSuccess(string message, string? title = null, int stageNumber = -1)
        {
            string successTitle = title ?? ErrorMessages.GetErrorMessage("SuccessTitle");
            if (stageNumber > 0)
            {
                string stageSuccessMessage = string.Format(ErrorMessages.GetErrorMessage("StageSuccessMessage"), stageNumber);
                MessageBox.Show(stageSuccessMessage, successTitle, MessageBoxButton.OK, MessageBoxImage.Information);
            }
            else
            {
                MessageBox.Show(message, successTitle, MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void CheckVaporizerButton() { _uiHelper.CheckVaporizerButton(); }

        public void UncheckVaporizerButton()
        {
            _uiHelper.UncheckVaporizerButton();
            _currentVoltageUpdateTimerManager.Stop();
        }

        private void SetShutterImageToClosed() { _uiHelper.SetShutterImageToClosed(); ; }
        private void SetShutterImageToOpened() { _uiHelper.SetShutterImageToOpened(); }
        private void ColorizeOpenShutterButton() { _uiHelper.ColorizeOpenShutterButton(OpenShutterButton, CloseShutterButton, StopStepMotorButton); }
        private void ColorizeCloseShutterButton() { _uiHelper.ColorizeCloseShutterButton(OpenShutterButton, CloseShutterButton, StopStepMotorButton); }
        private void ColorizeStopStepMotorButton() { _uiHelper.ColorizeStopStepMotorButton(OpenShutterButton, CloseShutterButton, StopStepMotorButton); }

        private void SetDisabledOpenShutterButton()
        {
            OpenShutterButton.IsEnabled = false;
            CloseShutterButton.IsEnabled = true;
        }

        private void SetDisabledCloseShutterButton()
        {
            OpenShutterButton.IsEnabled = true;
            CloseShutterButton.IsEnabled = false;
        }

        private void SetEnableOpenCloseShutterButtons()
        {
            OpenShutterButton.IsEnabled = true;
            CloseShutterButton.IsEnabled = true;
        }

        public void PowerSupplyConnect()
        {
            ExecuteWithErrorHandling(() =>
            {
                if (!_powerSupplyComPortManager.CheckComPort())
                    return;

                string comPort = _powerSupplyComPortManager.GetComPortName();
                _powerSupplyManager.Connect(comPort);
                _currentVoltageUpdateTimerManager.Start();
            }, UncheckVaporizerButton);
        }

        public void PowerSupplyTurnOn()
        {
            ExecuteWithErrorHandling(() =>
            {
                string comPort = _powerSupplyComPortManager.GetComPortName();
                _powerSupplyManager.TurnOn(comPort);
                _currentVoltageUpdateTimerManager.Start();
            }, UncheckVaporizerButton);
        }

        public void PowerSupplyReset()
        {
            ExecuteWithErrorHandling(() =>
            {
                string comPort = _powerSupplyComPortManager.GetComPortName();
                _powerSupplyManager.Reset(comPort);
            }, UncheckVaporizerButton);
        }

        public void PowerSupplyApplyCurrent(ushort current)
        {
            ExecuteWithErrorHandling(() =>
            {
                _powerSupplyManager.ApplyVoltage(current, PowerSupply.kdefault_Voltage);
            }, () =>
            {
                PowerSupplyTurnOff();
                UncheckVaporizerButton();
            });
        }

        public void PowerSupplyTurnOff()
        {
            ExecuteWithErrorHandling(() =>
            {
                string comPort = _powerSupplyComPortManager.GetComPortName();
                _powerSupplyManager.TurnOff(comPort);
                _currentVoltageUpdateTimerManager.Stop();
            }, UncheckVaporizerButton);
        }
        private void OpenShutterButton_Click(object sender, RoutedEventArgs e)
        {
            SetDisabledOpenShutterButton();
            OpenShutter();
        }

        private void CloseShutterButton_Click(object sender, RoutedEventArgs e)
        {
            SetDisabledCloseShutterButton();
            CloseShutter();
        }

        private void StopStepMotorButton_Click(object sender, RoutedEventArgs e)
        {
            SetEnableOpenCloseShutterButtons();
            StopStepMotor();
        }

        private void ExecuteWithErrorHandling(Action action, Action? onError = null)
        {
            try
            {
                action();
            }
            catch (Exception ex)
            {
                _scenariosWindow?.StopProgram(ex);
                ShowError(ex.Message);
                onError?.Invoke();
            }
        }

        /// Main functions
        private void AddScenarioButton_Click(object sender, RoutedEventArgs e)
        {
            _scenariosWindow = new ScenariosWindow(this);
            _scenariosWindow.Show();
            AddScenarioButton.IsEnabled = false;
        }
        public async Task StartScenarioForStage(ushort current, TimeSpan duration)
        {
            if (!AreComPortsValid())
                return;

            if (!_powerSupplyManager.IsConnected())
            {
                string warningMessage = ErrorMessages.GetErrorMessage("PowerSupplyConnectionWarning");
                ShowWarning(warningMessage);
                return;
            }

            string systemWorkingLabel = ErrorMessages.GetErrorMessage("SystemWorkingLabel");
            _uiHelper.CustomizeSystemStateLabel(systemWorkingLabel, Colors.Green);

            try
            {
                PowerSupplyTurnOn();
                PowerSupplyApplyCurrent(current);
                PowerSupplyUpdateCurrentVoltage(); // Reads specific register for the current and voltage and updating labels in UI
                PowerSupplyReset(); // Resets specific register that needed to correctly manage power supply after rebooting

                // Wait for the duration of the stage 
                await Task.Delay(duration);
            }
            catch (Exception ex)
            {
                ShowError(ex.Message);
            }
        }
        private void VaporizerButtonBase_Checked(object sender, RoutedEventArgs e)
        {
            if (_powerSupplyManager.IsConnected())
                return;
            CheckVaporizerButton();
            PowerSupplyConnect();
        }

        private void VaporizerButtonBase_Unchecked(object sender, RoutedEventArgs e)
        {
            if (!_powerSupplyManager.IsConnected())
                return;
            UncheckVaporizerButton();
            PowerSupplyTurnOff();
        }

        private void Window_Closed(object sender, EventArgs e)
        {
            if (_powerSupplyManager.IsConnected())
                PowerSupplyTurnOff();
            if (_stepMotorManager.IsConnected())
                StopStepMotor();
            _scenariosWindow?.Close();
        }

        private void ScanComPortsButton_Click(object sender, RoutedEventArgs e) { UpdateComPorts(); }
    }
}
