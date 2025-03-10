using System.Globalization;
using System.Resources;

namespace TusurUI.Logs
{
    /// <summary>
    /// Provides functionality to retrieve and manage localized log messages.
    /// </summary>
    public static class LogMessages
    {
        // ResourceManager to access the resources for localized log messages.
        private static ResourceManager resourceManager = new ResourceManager("TusurUI.Resources.LogMessages", typeof(LogMessages).Assembly);

        /// <summary>
        /// Gets the localized log message for the specified key.
        /// </summary>
        /// <param name="key">The key of the log message.</param>
        /// <returns>The localized log message or a default message if the key is not found.</returns>
        public static string GetLogMessage(string key)
        {
            return resourceManager.GetString(key, CultureInfo.CurrentUICulture) ?? $"[{key}] not found";
        }

        /// <summary>
        /// Sets the current UI culture for log messages.
        /// </summary>
        /// <param name="language">The language code to set the culture to.</param>
        public static void SetLanguage(string language) { CultureInfo.CurrentUICulture = new CultureInfo(language); }
    }
}
