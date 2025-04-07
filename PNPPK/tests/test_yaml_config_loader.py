import os
import sys
import time
import yaml
import pytest
import tempfile
import logging
import psutil
import memory_profiler
from unittest.mock import patch, mock_open

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.yaml_config_loader import (
    YAMLConfigLoader,
    YAMLConfigFileNotFoundError,
    YAMLConfigFileFormatError,
    YAMLConfigLoaderException,
)

# Setup logging for performance tests
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_yaml_file():
    """Fixture that creates a temporary valid YAML file."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as temp:
        temp.write(
            """
        relay:
          baudrate: 115200
          parity: N
          data_bit: 8
          stop_bit: 1
          slave_id: 16
          timeout: 50
        """
        )
        temp_name = temp.name

    yield temp_name

    # Cleanup - remove the temporary file
    try:
        os.unlink(temp_name)
    except:
        pass


@pytest.fixture
def invalid_yaml_file():
    """Fixture that creates a temporary invalid YAML file."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as temp:
        temp.write(
            """
        relay:
          baudrate: 115200
          parity: N
        # This line has improper indentation
        data_bit: 8
          stop_bit: 1
          slave_id: 16
          timeout: 50
        """
        )
        temp_name = temp.name

    yield temp_name

    # Cleanup - remove the temporary file
    try:
        os.unlink(temp_name)
    except:
        pass


@pytest.fixture
def large_yaml_file():
    """Fixture that creates a temporary large YAML file for stress testing."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as temp:
        # Create a large YAML file with 10,000 items
        temp.write("items:\n")
        for i in range(10000):
            temp.write(f"  item_{i}:\n")
            temp.write(f"    value: {i}\n")
            temp.write(f"    name: 'name_{i}'\n")
            temp.write(f"    enabled: {bool(i % 2)}\n")

        temp_name = temp.name

    yield temp_name

    # Cleanup - remove the temporary file
    try:
        os.unlink(temp_name)
    except:
        pass


# ============================================================================
# Basic Tests - Clean Tests
# ============================================================================


def test_load_config_valid_file_clean(valid_yaml_file):
    """Clean test: Load a valid YAML configuration file."""
    config = YAMLConfigLoader.load_config(valid_yaml_file)

    # Verify the loaded configuration
    assert isinstance(config, dict)
    assert "relay" in config
    assert config["relay"]["baudrate"] == 115200
    assert config["relay"]["parity"] == "N"
    assert config["relay"]["data_bit"] == 8
    assert config["relay"]["stop_bit"] == 1
    assert config["relay"]["slave_id"] == 16
    assert config["relay"]["timeout"] == 50


def test_load_config_file_not_found_clean():
    """Clean test: Handle a missing configuration file."""
    non_existent_file = "/path/to/non/existent/file.yaml"

    with pytest.raises(YAMLConfigFileNotFoundError) as excinfo:
        YAMLConfigLoader.load_config(non_existent_file)

    assert non_existent_file == excinfo.value.file_path
    assert "Configuration file not found" in str(excinfo.value)


def test_load_config_invalid_format_clean(invalid_yaml_file):
    """Clean test: Handle an invalid YAML format."""
    with pytest.raises(YAMLConfigFileFormatError) as excinfo:
        YAMLConfigLoader.load_config(invalid_yaml_file)

    assert invalid_yaml_file == excinfo.value.file_path
    assert "Invalid YAML format" in str(excinfo.value)
    assert isinstance(excinfo.value.error, yaml.YAMLError)


# ============================================================================
# Basic Tests - Dirty Tests
# ============================================================================


def test_load_config_empty_file_dirty():
    """Dirty test: Load an empty YAML file."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as temp:
        temp_name = temp.name

    try:
        # Empty file should return None from yaml.safe_load
        config = YAMLConfigLoader.load_config(temp_name)
        assert config is None
    finally:
        os.unlink(temp_name)


def test_load_config_permission_error_dirty():
    """Dirty test: Handle permission error when accessing file."""
    with patch("builtins.open", side_effect=PermissionError("Permission denied")):
        with pytest.raises(YAMLConfigLoaderException) as excinfo:
            YAMLConfigLoader.load_config("some_file.yaml")

        assert "Unexpected error loading configuration file" in str(excinfo.value)
        assert "Permission denied" in str(excinfo.value)


def test_load_config_unexpected_error_dirty():
    """Dirty test: Handle unexpected errors during loading."""
    with patch("builtins.open", mock_open()):
        with patch("yaml.safe_load", side_effect=Exception("Unexpected error")):
            with pytest.raises(YAMLConfigLoaderException) as excinfo:
                YAMLConfigLoader.load_config("some_file.yaml")

            assert "Unexpected error loading configuration file" in str(excinfo.value)


def test_load_config_invalid_input_types_dirty():
    """Dirty test: Try to load config with invalid input types."""
    # Test with None
    with pytest.raises(Exception):
        YAMLConfigLoader.load_config(None)  # type: ignore

    # Test with integer
    with pytest.raises(Exception):
        YAMLConfigLoader.load_config(123)  # type: ignore

    # Test with list
    with pytest.raises(Exception):
        YAMLConfigLoader.load_config([])  # type: ignore


def test_yaml_file_with_duplicates_dirty():
    """Dirty test: Handle YAML file with duplicate keys."""
    yaml_content = """
    relay:
      baudrate: 115200
      baudrate: 9600  # Duplicate key
    """

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as temp:
        temp.write(yaml_content)
        temp_name = temp.name

    try:
        # In YAML, when duplicate keys exist, the last one will be used
        config = YAMLConfigLoader.load_config(temp_name)
        assert config["relay"]["baudrate"] == 9600
    finally:
        os.unlink(temp_name)


# ============================================================================
# Functional Tests
# ============================================================================


def test_load_config_with_complex_yaml_functional():
    """Functional test: Load a complex YAML file with nested structures."""
    yaml_content = """
    devices:
      gfr:
        connection:
          baudrate: 38400
          parity: N
          data_bit: 8
          stop_bit: 1
          slave_id: 1
          timeout: 50
        settings:
          default_flow: 50.0
          min_flow: 0.0
          max_flow: 100.0
          units: cm3/min
      relay:
        connection:
          baudrate: 115200
          parity: N
          data_bit: 8
          stop_bit: 1
          slave_id: 16
          timeout: 50
        settings:
          channels:
            - name: channel1
              default: off
            - name: channel2
              default: "on"
    logging:
      level: INFO
      file: logs/app.log
      format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    """

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as temp:
        temp.write(yaml_content)
        temp_name = temp.name

    try:
        config = YAMLConfigLoader.load_config(temp_name)

        # Verify the complex structure was loaded correctly
        assert config["devices"]["gfr"]["connection"]["baudrate"] == 38400
        assert (
            config["devices"]["relay"]["settings"]["channels"][0]["name"] == "channel1"
        )
        assert (
            str(config["devices"]["relay"]["settings"]["channels"][1]["default"])
            == "on"
        )
    finally:
        os.unlink(temp_name)


def test_load_config_with_different_data_types_functional():
    """Functional test: Load YAML with various data types."""
    yaml_content = """
    string_value: "text"
    integer_value: 42
    float_value: 3.14
    boolean_value: true
    null_value: null
    list_value: 
      - item1
      - item2
      - 3
    date_value: 2023-01-01
    binary_data: !!binary |
      R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7
    """

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as temp:
        temp.write(yaml_content)
        temp_name = temp.name

    try:
        config = YAMLConfigLoader.load_config(temp_name)

        # Verify different data types
        assert config["string_value"] == "text"
        assert config["integer_value"] == 42
        assert config["float_value"] == 3.14
        assert config["boolean_value"] is True
        assert config["null_value"] is None
        assert config["list_value"] == ["item1", "item2", 3]
        assert config["date_value"].year == 2023
        assert isinstance(config["binary_data"], bytes)
    finally:
        os.unlink(temp_name)


def test_exception_hierarchy_functional():
    """Functional test: Verify the exception hierarchy."""
    # Test that YAMLConfigFileNotFoundError is a subclass of YAMLConfigLoaderException
    assert issubclass(YAMLConfigFileNotFoundError, YAMLConfigLoaderException)

    # Test that YAMLConfigFileFormatError is a subclass of YAMLConfigLoaderException
    assert issubclass(YAMLConfigFileFormatError, YAMLConfigLoaderException)

    # Create instances of exceptions
    not_found_exception = YAMLConfigFileNotFoundError("test.yaml")
    format_exception = YAMLConfigFileFormatError("test.yaml", Exception("Test error"))

    # Verify properties of exceptions
    assert not_found_exception.file_path == "test.yaml"
    assert format_exception.file_path == "test.yaml"
    assert isinstance(format_exception.error, Exception)
    assert str(format_exception.error) == "Test error"


# ============================================================================
# Integration Tests
# ============================================================================


def test_config_file_with_environment_variables_integration():
    """Integration test: Test loading a YAML file with environment variables."""
    # Set environment variables for testing
    os.environ["TEST_BAUDRATE"] = "9600"
    os.environ["TEST_PARITY"] = "E"

    yaml_content = """
    relay:
      baudrate: ${TEST_BAUDRATE}
      parity: ${TEST_PARITY}
      data_bit: 8
    """

    # Use a custom loader function that handles environment variables
    def custom_env_loader(file_path):
        with open(file_path, "r") as file:
            content = file.read()
            # Simple environment variable replacement
            for key, value in os.environ.items():
                content = content.replace(f"${{{key}}}", value)
            return yaml.safe_load(content)

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as temp:
        temp.write(yaml_content)
        temp_name = temp.name

    try:
        # Test with custom loader function
        with patch.object(
            YAMLConfigLoader, "load_config", side_effect=custom_env_loader
        ):
            config = YAMLConfigLoader.load_config(temp_name)

            # Verify environment variables were replaced
            assert str(config["relay"]["baudrate"]) == "9600"
    finally:
        os.unlink(temp_name)


def test_load_config_in_application_context_integration(valid_yaml_file):
    """Integration test: Test loading config in an application context."""

    # Simulate a simple application that uses the config
    class MockApplication:
        def __init__(self, config_file):
            self.config = YAMLConfigLoader.load_config(config_file)
            self.relay_baudrate = self.config["relay"]["baudrate"]
            self.relay_parity = self.config["relay"]["parity"]
            self.relay_timeout = self.config["relay"]["timeout"]

        def initialize_relay(self):
            # Simulate relay initialization
            return {
                "baudrate": self.relay_baudrate,
                "parity": self.relay_parity,
                "timeout": self.relay_timeout,
            }

    # Create and test application
    app = MockApplication(valid_yaml_file)
    relay_config = app.initialize_relay()

    # Verify application used the config correctly
    assert relay_config["baudrate"] == 115200
    assert relay_config["parity"] == "N"
    assert relay_config["timeout"] == 50


def test_load_multiple_configs_integration():
    """Integration test: Load and merge multiple configuration files."""
    # Create two config files
    base_yaml = """
    app:
      name: TestApp
      version: 1.0
    database:
      host: localhost
      port: 5432
    """

    override_yaml = """
    app:
      version: 1.1
    database:
      username: admin
      password: secure123
    """

    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".yaml", delete=False
    ) as base_file:
        base_file.write(base_yaml)
        base_file_name = base_file.name

    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".yaml", delete=False
    ) as override_file:
        override_file.write(override_yaml)
        override_file_name = override_file.name

    try:
        # Load both configs
        base_config = YAMLConfigLoader.load_config(base_file_name)
        override_config = YAMLConfigLoader.load_config(override_file_name)

        # Implement a simple merge function
        def merge_configs(base, override):
            result = base.copy()
            for key, value in override.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = merge_configs(result[key], value)
                else:
                    result[key] = value
            return result

        # Merge configs
        merged_config = merge_configs(base_config, override_config)

        # Verify merged config
        assert merged_config["app"]["name"] == "TestApp"  # From base
        assert merged_config["app"]["version"] == 1.1  # Overridden
    finally:
        os.unlink(base_file_name)
        os.unlink(override_file_name)


# ============================================================================
# Stress Tests
# ============================================================================


def test_memory_usage_stress(large_yaml_file):
    """Stress test: Measure memory usage when loading a large YAML file."""
    # Get initial memory usage
    process = psutil.Process(os.getpid())
    memory_before = process.memory_info().rss / 1024 / 1024  # Convert to MB

    # Profile memory usage
    @memory_profiler.profile
    def load_large_file():
        return YAMLConfigLoader.load_config(large_yaml_file)

    # Load the large file
    start_time = time.time()
    config = load_large_file()
    end_time = time.time()

    # Get memory usage after loading
    memory_after = process.memory_info().rss / 1024 / 1024  # Convert to MB
    memory_diff = memory_after - memory_before

    # Log performance metrics
    logger.info(
        f"Memory usage: Before={memory_before:.2f}MB, After={memory_after:.2f}MB, Diff={memory_diff:.2f}MB"
    )
    logger.info(f"Time to load large file: {end_time - start_time:.3f} seconds")

    # Verify file was loaded correctly
    assert isinstance(config, dict)
    assert "items" in config
    assert len(config["items"]) == 10000
    assert config["items"]["item_5000"]["value"] == 5000


def test_repeated_loads_stress(valid_yaml_file):
    """Stress test: Repeatedly load a configuration file many times."""
    start_time = time.time()
    iterations = 1000

    # Perform many load operations
    for i in range(iterations):
        config = YAMLConfigLoader.load_config(valid_yaml_file)
        assert config["relay"]["baudrate"] == 115200

    end_time = time.time()
    total_time = end_time - start_time
    avg_time_per_load = total_time / iterations

    # Log performance metrics
    logger.info(f"Completed {iterations} load operations in {total_time:.3f} seconds")
    logger.info(f"Average time per load: {avg_time_per_load * 1000:.3f} ms")


def test_concurrent_access_simulation_stress(valid_yaml_file):
    """Stress test: Simulate concurrent access to the loader."""
    import threading

    # Number of concurrent threads
    thread_count = 20
    iterations_per_thread = 50
    errors = []

    def worker(thread_id):
        try:
            for i in range(iterations_per_thread):
                config = YAMLConfigLoader.load_config(valid_yaml_file)
                assert config["relay"]["baudrate"] == 115200
        except Exception as e:
            errors.append(f"Thread {thread_id} error: {str(e)}")

    start_time = time.time()

    # Create and start threads
    threads = []
    for i in range(thread_count):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    end_time = time.time()
    total_time = end_time - start_time

    # Log performance metrics
    logger.info(
        f"Completed {thread_count * iterations_per_thread} load operations across {thread_count} threads"
    )
    logger.info(f"Total time: {total_time:.3f} seconds")
    logger.info(
        f"Average time per operation: {total_time / (thread_count * iterations_per_thread) * 1000:.3f} ms"
    )

    # Check for errors
    assert not errors, f"Errors occurred during concurrent access: {errors}"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
