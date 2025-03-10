using System.Windows.Controls;
using System.Windows.Threading;
using TusurUI.Errors;
using TusurUI.Helpers;
using TusurUI.Interfaces;

public class PowerSupplyTimerManager : IPowerSupplyTimerManager
{
    private const int k_SecondsInHour = 3600;
    private const int k_SecondsInMinute = 60;
    private const int k_MaxHours = 24;
    private const int k_MaxMinutes = 60;
    private const int k_MaxSeconds = 60;

    private readonly TextBox _timerTextBoxHours;
    private readonly TextBox _timerTextBoxMins;
    private readonly TextBox _timerTextBoxSecs;
    private readonly ProgressBar _progressBar;
    private DispatcherTimer? _timerCountdown;
    protected int _remainingSeconds;
    public bool IsDirectCountdown { get; set; }
    private readonly Action _turnOffPowerSupply;
    public bool IsRunning { get; private set; }

    public PowerSupplyTimerManager(TextBox timerTextBoxHours, TextBox timerTextBoxMins, TextBox timerTextBoxSecs, ProgressBar progressBar, Action turnOffPowerSupply)
    {
        _timerTextBoxHours = timerTextBoxHours ?? throw new ArgumentNullException(nameof(timerTextBoxHours));
        _timerTextBoxMins = timerTextBoxMins ?? throw new ArgumentNullException(nameof(timerTextBoxMins));
        _timerTextBoxSecs = timerTextBoxSecs ?? throw new ArgumentNullException(nameof(timerTextBoxSecs));
        _progressBar = progressBar ?? throw new ArgumentNullException(nameof(progressBar));
        _turnOffPowerSupply = turnOffPowerSupply ?? throw new ArgumentNullException(nameof(turnOffPowerSupply));
    }

    public void StartCountdown(bool isReverseCountdown)
    {
        IsDirectCountdown = isReverseCountdown;

        bool hoursEmpty = string.IsNullOrWhiteSpace(_timerTextBoxHours.Text);
        bool minsEmpty = string.IsNullOrWhiteSpace(_timerTextBoxMins.Text);
        bool secsEmpty = string.IsNullOrWhiteSpace(_timerTextBoxSecs.Text);

        if (hoursEmpty && minsEmpty && secsEmpty)
        {
            if (isReverseCountdown)
            {
                UIHelper.MarkTextBoxAsInvalid(_timerTextBoxHours);
                UIHelper.MarkTextBoxAsInvalid(_timerTextBoxMins);
                UIHelper.MarkTextBoxAsInvalid(_timerTextBoxSecs);
                string errorMessage = ErrorMessages.Compose(ErrorMessages.GetErrorMessage("EmptyTimeTextFields"));
                throw new ArgumentException(errorMessage);
            }
            else
            {
                _remainingSeconds = 0;
                SetTextBoxesReadOnly(true);
            }
        }
        else
        {
            if (!IsValidTimeInput(_timerTextBoxHours.Text, k_MaxHours, out int hours) ||
                !IsValidTimeInput(_timerTextBoxMins.Text, k_MaxMinutes, out int minutes) ||
                !IsValidTimeInput(_timerTextBoxSecs.Text, k_MaxSeconds, out int seconds))
            {
                string errorMessage = ErrorMessages.Compose(ErrorMessages.GetErrorMessage("InvalidTimeTextField"));
                throw new ArgumentException(errorMessage);
            }

            _remainingSeconds = (hours * k_SecondsInHour) + (minutes * k_SecondsInMinute) + seconds;

            if (_remainingSeconds > 0)
            {
                SetTextBoxesReadOnly(true);
            }
            else
            {
                _remainingSeconds = 0;
            }
        }

        _progressBar.Minimum = 0;
        _progressBar.Maximum = _remainingSeconds;
        _progressBar.Value = 0;

        _timerCountdown = new DispatcherTimer
        {
            Interval = TimeSpan.FromSeconds(1)
        };
        _timerCountdown.Tick += TimerCountdown_Tick;
        _timerCountdown.Start();
        IsRunning = true;
    }
    protected virtual void TimerCountdown_Tick(object? sender, EventArgs e)
    {
        if (!IsDirectCountdown)
        {
            _remainingSeconds++;
        }
        else
        {
            if (_remainingSeconds > 0)
            {
                _remainingSeconds--;
            }
            else
            {
                _timerCountdown?.Stop();
                _turnOffPowerSupply?.Invoke();
                ResetTimer();
                return;
            }
        }

        int hours = _remainingSeconds / k_SecondsInHour;
        int minutes = (_remainingSeconds % k_SecondsInHour) / k_SecondsInMinute;
        int seconds = _remainingSeconds % k_SecondsInMinute;

        _timerTextBoxHours.Text = hours.ToString("D2");
        _timerTextBoxMins.Text = minutes.ToString("D2");
        _timerTextBoxSecs.Text = seconds.ToString("D2");

        _progressBar.Value = IsDirectCountdown ? (_progressBar.Maximum - _remainingSeconds) : _remainingSeconds;
    }
    public void ResetTimer()
    {
        _timerCountdown?.Stop();
        _timerCountdown = null;
        _remainingSeconds = 0;
        IsRunning = false;

        _progressBar.Minimum = 0;
        _progressBar.Maximum = 1;
        _progressBar.Value = 0;

        ClearTextBoxes();
        SetTextBoxesReadOnly(false);
    }

    private bool IsValidTimeInput(string text, int max, out int value)
    {
        if (text == "")
            text = "0";
        bool isValid = int.TryParse(text, out value) && value >= 0 && value < max;
        return isValid;
    }

    private void SetTextBoxesReadOnly(bool isReadOnly)
    {
        _timerTextBoxHours.IsReadOnly = isReadOnly;
        _timerTextBoxMins.IsReadOnly = isReadOnly;
        _timerTextBoxSecs.IsReadOnly = isReadOnly;
    }

    private void ClearTextBoxes()
    {
        _timerTextBoxHours.Text = string.Empty;
        _timerTextBoxMins.Text = string.Empty;
        _timerTextBoxSecs.Text = string.Empty;
    }
}
