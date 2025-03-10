using System.Globalization;
using System.Resources;

namespace TusurUI.Errors
{
    public static class ErrorMessages
    {
        private static ResourceManager resourceManager = new ResourceManager("TusurUI.Resources.ErrorMessages", typeof(ErrorMessages).Assembly);

        /// <summary>
        /// Gets the localized error message for the specified key.
        /// </summary>
        /// <param name="key">The key of the error message.</param>
        /// <returns>The localized error message or a default message if the key is not found.</returns>
        public static string GetErrorMessage(string key) { return resourceManager.GetString(key, CultureInfo.CurrentUICulture) ?? $"[{key}] not found"; }

        /// <summary>
        /// Composes an error message by concatenating multiple parts.
        /// </summary>
        /// <param name="messages">The error message parts to concatenate.</param>
        /// <returns>The composed error message.</returns>
        public static string Compose(params string[] messages) { return string.Join(" ", messages); }

        /// <summary>
        /// Sets the current UI culture for error messages.
        /// </summary>
        /// <param name="language">The language code to set the culture to.</param>
        public static void SetLanguage(string language) { CultureInfo.CurrentUICulture = new CultureInfo(language); }
    }
}
