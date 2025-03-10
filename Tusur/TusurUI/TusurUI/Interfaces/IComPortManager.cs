using System.Windows.Controls;

namespace TusurUI.Interfaces
{
    /**
     * @interface IComPortManager
     * @brief Interface for managing COM ports in the application.
     *
     * This interface provides methods to populate a ComboBox with available COM ports,
     * check the validity of the selected COM port, and retrieve the name of the selected COM port.
     */
    public interface IComPortManager
    {
        /**
         * @brief Populates the ComboBox with available COM ports.
         *
         * This method retrieves the list of available COM ports on the system and populates
         * the associated ComboBox with these ports.
         */
        void PopulateComPortComboBox(ComboBox otherComboBox);

        /**
         * @brief Checks if the selected COM port is valid.
         * @return True if the selected COM port is valid, otherwise false.
         *
         * This method checks whether a valid COM port has been selected from the ComboBox.
         */
        bool CheckComPort();

        /**
         * @brief Checks if a COM port is selected.
         * @return True if a COM port is selected, otherwise false.
         *
         * This method verifies if any COM port has been selected from the ComboBox.
         */
        bool IsComPortSelected();

        /**
        * @brief Checks if a COM port is not selected.
        * @return True if no COM port is selected, otherwise false.
        *
        * This method verifies if no COM port has been selected from the ComboBox.
        */
        bool IsComPortNotSelected();

        /**
         * @brief Gets the name of the selected COM port.
         * @return The name of the selected COM port.
         *
         * This method retrieves the name of the currently selected COM port from the ComboBox.
         */
        string GetComPortName();
    }
}
