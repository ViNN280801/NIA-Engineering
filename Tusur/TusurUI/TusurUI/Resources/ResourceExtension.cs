using System;
using System.Windows.Markup;
using TusurUI.Errors;

namespace TusurUI.Resources
{
    public class ResourceExtension : MarkupExtension
    {
        public string? Key { get; set; }

        public override object ProvideValue(IServiceProvider serviceProvider)
        {
            if (Key == null)
                return string.Empty;

            var value = ErrorMessages.GetErrorMessage(Key);
            return value ?? string.Empty;
        }
    }
}
