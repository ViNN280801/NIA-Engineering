using System.Globalization;

namespace TusurUI.Resources
{
    public static class ResourceHelper
    {
        public static void ChangeCulture(string cultureCode)
        {
            CultureInfo newCulture = new CultureInfo(cultureCode);
            CultureInfo.CurrentCulture = newCulture;
            CultureInfo.CurrentUICulture = newCulture;
        }
    }
}
