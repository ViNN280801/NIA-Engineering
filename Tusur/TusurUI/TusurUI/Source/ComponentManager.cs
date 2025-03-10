using System.Windows.Controls;
using System.Windows.Media.Imaging;

namespace TusurUI.Source
{
    public static class ComponentManager
    {
        public static void ChangeIndicatorPicture(Image indicator, string imagePath)
        {
            if (indicator == null)
                throw new ArgumentNullException(nameof(indicator));
            if (string.IsNullOrWhiteSpace(imagePath))
                throw new ArgumentNullException(nameof(imagePath));

            var image = new BitmapImage();
            image.BeginInit();
            image.UriSource = new Uri(imagePath, UriKind.Relative);
            image.EndInit();

            indicator.Source = image;
        }

        public static BitmapImage? GetIndicatorImage(Image indicator)
        {
            if (indicator == null)
                throw new Exception(nameof(indicator));
            return indicator.Source as BitmapImage;
        }
    }
}
