# ПНППК

## How to run tests?

```bash
pytest .\tests\ -v --log-cli-level=INFO
```

### Flags:

- `-v` - verbosing
- `--log-cli-level=<LOG_LEVEL>` - sets the log level

### Example of running:

```
(venv) PS D:\Work\PNPPK> pytest .\tests\ -v --log-cli-level=INFO
=================================================================== test session starts ===================================================================
platform win32 -- Python 3.12.7, pytest-8.3.5, pluggy-1.5.0 -- D:\Work\PNPPK\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Work\PNPPK
collected 111 items

tests/test_auto_dialog.py::test_show_message_dialog_auto_closing PASSED                                                                              [  0%]
tests/test_auto_dialog.py::test_file_dialog_auto_closing PASSED                                                                                      [  1%]
tests/test_auto_dialog.py::test_input_dialog_auto_closing PASSED                                                                                     [  2%]
tests/test_auto_dialog.py::test_gfr_window_dialog_auto_closing PASSED                                                                                [  3%]
tests/test_controllers_integration.py::TestControllersIntegration::test_sequential_operations PASSED                                                 [  4%]
tests/test_controllers_integration.py::TestControllersIntegration::test_concurrent_operations PASSED                                                 [  5%]
tests/test_controllers_integration.py::TestControllersIntegration::test_shared_port_handling SKIPPED (Нужны реальные устройства (запустите с --r...) [  6%]
tests/test_controllers_integration.py::TestControllersIntegration::test_error_propagation PASSED                                                     [  7%]
tests/test_controllers_integration.py::TestControllersIntegration::test_device_disconnection_handling PASSED                                         [  8%]
tests/test_controllers_integration.py::TestControllersWorkflow::test_gas_flow_experiment SKIPPED (Нужны реальные устройства (запустите с --real-...) [  9%]
tests/test_gfr_controller.py::TestGFRControllerUnit::test_init_creates_modbus_client SKIPPED (Нужны реальные устройства (запустите с --real-devi...) [  9%]
tests/test_gfr_controller.py::TestGFRControllerUnit::test_init_connection_failure SKIPPED (Нужны реальные устройства (запустите с --real-devices))   [ 10%]
tests/test_gfr_controller.py::TestGFRControllerUnit::test_turnon_calls_init PASSED                                                                   [ 11%]
tests/test_gfr_controller.py::TestGFRControllerUnit::test_turnoff_calls_close PASSED                                                                 [ 12%]
tests/test_gfr_controller.py::TestGFRControllerUnit::test_setflow_writes_to_registers PASSED                                                         [ 13%]
tests/test_gfr_controller.py::TestGFRControllerUnit::test_getflow_reads_from_register PASSED                                                         [ 14%]
tests/test_gfr_controller.py::TestGFRControllerUnit::test_getflow_error_handling PASSED                                                              [ 15%]
tests/test_gfr_controller.py::TestGFRControllerUnit::test_getflow_no_registers_attr PASSED                                                           [ 16%]
tests/test_gfr_controller.py::TestGFRControllerUnit::test_is_connected PASSED                                                                        [ 17%]
tests/test_gfr_controller.py::TestGFRControllerUnit::test_is_disconnected PASSED                                                                     [ 18%]
tests/test_gfr_controller.py::TestGFRControllerUnit::test_set_gas PASSED                                                                             [ 18%]
tests/test_gfr_controller.py::TestGFRControllerFunctional::test_full_flow_lifecycle SKIPPED (Нужны реальные устройства (запустите с --real-devices)) [ 19%]
tests/test_gfr_controller.py::TestGFRControllerFunctional::test_multiple_setflow_operations PASSED                                                   [ 20%]
tests/test_gfr_controller.py::TestGFRControllerFunctional::test_error_handling_during_connection SKIPPED (Нужны реальные устройства (запустите с...) [ 21%]
tests/test_gfr_controller.py::TestGFRControllerIntegration::test_integration_with_modbus_utils PASSED                                                [ 22%]
tests/test_gfr_controller.py::TestGFRControllerIntegration::test_connection_retry_mechanism SKIPPED (Нужны реальные устройства (запустите с --re...) [ 23%]
tests/test_gfr_controller.py::TestGFRControllerIntegration::test_connection_with_environment_variable SKIPPED (Нужны реальные устройства (запуст...) [ 24%]
tests/test_gfr_controller.py::TestGFRControllerStress::test_memory_usage SKIPPED (Нужны реальные устройства (запустите с --real-devices))            [ 25%]
tests/test_gfr_controller.py::TestGFRControllerStress::test_repeated_operations
---------------------------------------------------------------------- live log call ----------------------------------------------------------------------
INFO     tests.test_gfr_controller:test_gfr_controller.py:467 Executed 1000 operations in 0.08 seconds
INFO     tests.test_gfr_controller:test_gfr_controller.py:468 Average operation time: 0.08 ms
PASSED                                                                                                                                               [ 26%]
tests/test_modbus_utils.py::test_set_get_reset_last_error_clean PASSED                                                                               [ 27%]
tests/test_modbus_utils.py::test_set_last_error_wrong_type_dirty PASSED                                                                              [ 27%]
tests/test_modbus_utils.py::test_set_last_error_empty_string_dirty PASSED                                                                            [ 28%]
tests/test_modbus_utils.py::test_set_last_error_none_dirty PASSED                                                                                    [ 29%]
tests/test_modbus_utils.py::test_global_last_error_shared_state_dirty PASSED                                                                         [ 30%]
tests/test_modbus_utils.py::test_reset_last_error_multiple_times_dirty PASSED                                                                        [ 31%]
tests/test_modbus_utils.py::test_modbus_operation_basic_clean PASSED                                                                                 [ 32%]
tests/test_modbus_utils.py::test_modbus_operation_device_not_initialized_dirty PASSED                                                                [ 33%]
tests/test_modbus_utils.py::test_modbus_operation_exception_in_function_dirty PASSED                                                                 [ 34%]
tests/test_modbus_utils.py::test_modbus_operation_exception_with_no_close_method_dirty PASSED                                                        [ 35%]
tests/test_modbus_utils.py::test_modbus_operation_function_returns_error_dirty PASSED                                                                [ 36%]
tests/test_modbus_utils.py::test_modbus_operation_exception_during_cleanup_dirty PASSED                                                              [ 36%]
tests/test_modbus_utils.py::test_modbus_operation_custom_return_values_clean PASSED                                                                  [ 37%]
tests/test_modbus_utils.py::test_modbus_operation_skip_device_check_dirty PASSED                                                                     [ 38%]
tests/test_modbus_utils.py::test_modbus_operation_preserve_return_value_clean PASSED                                                                 [ 39%]
tests/test_modbus_utils.py::test_modbus_operation_preserve_return_value_error_dirty PASSED                                                           [ 40%]
tests/test_modbus_utils.py::test_modbus_operation_device_attr_with_self_prefix_dirty PASSED                                                          [ 41%]
tests/test_modbus_utils.py::test_modbus_operation_nonexistent_device_attr_dirty PASSED                                                               [ 42%]
tests/test_modbus_utils.py::test_modbus_operation_nested_device_attr_dirty PASSED                                                                    [ 43%]
tests/test_modbus_utils.py::test_modbus_operation_integration_clean PASSED                                                                           [ 44%]
tests/test_modbus_utils.py::test_modbus_operation_recursive_calls_dirty PASSED                                                                       [ 45%]
tests/test_modbus_utils.py::test_modbus_operation_async_method_simulation_dirty PASSED                                                               [ 45%]
tests/test_relay_controller.py::TestRelayControllerUnit::test_init_creates_modbus_client SKIPPED (Нужны реальные устройства (запустите с --real-...) [ 46%]
tests/test_relay_controller.py::TestRelayControllerUnit::test_init_connection_failure SKIPPED (Нужны реальные устройства (запустите с --real-dev...) [ 47%]
tests/test_relay_controller.py::TestRelayControllerUnit::test_turnon_calls_init_and_write_register PASSED                                            [ 48%]
tests/test_relay_controller.py::TestRelayControllerUnit::test_turnoff_calls_write_register_and_close PASSED                                          [ 49%]
tests/test_relay_controller.py::TestRelayControllerUnit::test_is_connected PASSED                                                                    [ 50%]
tests/test_relay_controller.py::TestRelayControllerUnit::test_is_disconnected PASSED                                                                 [ 51%]
tests/test_relay_controller.py::TestRelayControllerUnit::test_close_method PASSED                                                                    [ 52%]
tests/test_relay_controller.py::TestRelayControllerUnit::test_set_slave PASSED                                                                       [ 53%]
tests/test_relay_controller.py::TestRelayControllerFunctional::test_full_relay_lifecycle SKIPPED (Нужны реальные устройства (запустите с --real-...) [ 54%]
tests/test_relay_controller.py::TestRelayControllerFunctional::test_error_handling_during_connection SKIPPED (Нужны реальные устройства (запусти...) [ 54%]
tests/test_relay_controller.py::TestRelayControllerFunctional::test_turnon_turnoff_sequence SKIPPED (Нужны реальные устройства (запустите с --re...) [ 55%]
tests/test_relay_controller.py::TestRelayControllerIntegration::test_integration_with_modbus_utils PASSED                                            [ 56%]
tests/test_relay_controller.py::TestRelayControllerIntegration::test_connection_retry_mechanism SKIPPED (Нужны реальные устройства (запустите с ...) [ 57%]
tests/test_relay_controller.py::TestRelayControllerIntegration::test_connection_with_different_parameters SKIPPED (Нужны реальные устройства (за...) [ 58%]
tests/test_relay_controller.py::TestRelayControllerStress::test_memory_usage SKIPPED (Нужны реальные устройства (запустите с --real-devices))        [ 59%]
tests/test_relay_controller.py::TestRelayControllerStress::test_rapid_on_off_operations
---------------------------------------------------------------------- live log call ----------------------------------------------------------------------
INFO     tests.test_relay_controller:test_relay_controller.py:470 Executed 1000 operations in 0.02 seconds
INFO     tests.test_relay_controller:test_relay_controller.py:471 Average operation time: 0.02 ms
PASSED                                                                                                                                               [ 60%]
tests/test_relay_controller.py::TestRelayControllerStress::test_parallel_controller_operations SKIPPED (Нужны реальные устройства (запустите с -...) [ 61%]
tests/test_window.py::test_window_initialization_clean PASSED                                                                                        [ 62%]
tests/test_window.py::test_toggle_gfr_button_clean PASSED                                                                                            [ 63%]
tests/test_window.py::test_setpoint_handling_clean PASSED                                                                                            [ 63%]
tests/test_window.py::test_empty_setpoint_dirty PASSED                                                                                               [ 64%]
tests/test_window.py::test_invalid_setpoint_dirty PASSED                                                                                             [ 65%]
tests/test_window.py::test_gfr_not_connected_dirty PASSED                                                                                            [ 66%]
tests/test_window.py::test_setpoint_failure_dirty PASSED                                                                                             [ 67%]
tests/test_window.py::test_error_messages_dirty PASSED                                                                                               [ 68%]
tests/test_window.py::test_com_port_handling_functional PASSED                                                                                       [ 69%]
tests/test_window.py::test_open_close_connections_functional SKIPPED (Problems with calling real methods in the test)                                [ 70%]
tests/test_window.py::test_graph_management_functional PASSED                                                                                        [ 71%]
tests/test_window.py::test_data_saving_functional SKIPPED (Problems with calling method figure.savefig)                                              [ 72%]
tests/test_window.py::test_device_disconnection_detection_functional PASSED                                                                          [ 72%]
tests/test_window.py::test_gfr_relay_integration PASSED                                                                                              [ 73%]
tests/test_window.py::test_graph_updates_integration PASSED                                                                                          [ 74%]
tests/test_window.py::test_config_loading_integration PASSED                                                                                         [ 75%]
tests/test_window.py::test_button_click_gui PASSED                                                                                                   [ 76%]
tests/test_window.py::test_text_input_gui PASSED                                                                                                     [ 77%]
tests/test_window.py::test_combobox_selection_gui PASSED                                                                                             [ 78%]
tests/test_window.py::test_keyboard_shortcut_gui PASSED                                                                                              [ 79%]
tests/test_window.py::test_message_dialog_gui PASSED                                                                                                 [ 80%]
tests/test_window.py::test_window_resize_gui PASSED                                                                                                  [ 81%]
tests/test_window.py::test_splitter_gui PASSED                                                                                                       [ 81%]
tests/test_window.py::test_memory_usage_window_stress
---------------------------------------------------------------------- live log call ----------------------------------------------------------------------
INFO     tests.test_window:test_window.py:707 Memory usage: Before=135.77MB, After=135.86MB, Diff=0.09MB
INFO     tests.test_window:test_window.py:710 Time to create 3 windows: 0.015 seconds
INFO     tests.test_window:test_window.py:713 Average time per window: 0.005 seconds
PASSED                                                                                                                                               [ 82%]
tests/test_window.py::test_graph_large_dataset_stress
---------------------------------------------------------------------- live log call ----------------------------------------------------------------------
INFO     tests.test_window:test_window.py:753 Time to update plot with 1000 points: 0.000 seconds
INFO     tests.test_window:test_window.py:756 Average time per point: 0.000 ms
PASSED                                                                                                                                               [ 83%]
tests/test_window.py::test_rapid_ui_interaction_stress
---------------------------------------------------------------------- live log call ----------------------------------------------------------------------
INFO     tests.test_window:test_window.py:786 Time for 50 toggle operations: 0.000 seconds
INFO     tests.test_window:test_window.py:804 Time for 50 setpoint operations: 0.000 seconds
PASSED                                                                                                                                               [ 84%]
tests/test_yaml_config_loader.py::test_load_config_valid_file_clean PASSED                                                                           [ 85%]
tests/test_yaml_config_loader.py::test_load_config_file_not_found_clean PASSED                                                                       [ 86%]
tests/test_yaml_config_loader.py::test_load_config_invalid_format_clean PASSED                                                                       [ 87%]
tests/test_yaml_config_loader.py::test_load_config_empty_file_dirty PASSED                                                                           [ 88%]
tests/test_yaml_config_loader.py::test_load_config_permission_error_dirty PASSED                                                                     [ 89%]
tests/test_yaml_config_loader.py::test_load_config_unexpected_error_dirty PASSED                                                                     [ 90%]
tests/test_yaml_config_loader.py::test_load_config_invalid_input_types_dirty PASSED                                                                  [ 90%]
tests/test_yaml_config_loader.py::test_yaml_file_with_duplicates_dirty PASSED                                                                        [ 91%]
tests/test_yaml_config_loader.py::test_load_config_with_complex_yaml_functional PASSED                                                               [ 92%]
tests/test_yaml_config_loader.py::test_load_config_with_different_data_types_functional PASSED                                                       [ 93%]
tests/test_yaml_config_loader.py::test_exception_hierarchy_functional PASSED                                                                         [ 94%]
tests/test_yaml_config_loader.py::test_config_file_with_environment_variables_integration PASSED                                                     [ 95%]
tests/test_yaml_config_loader.py::test_load_config_in_application_context_integration PASSED                                                         [ 96%]
tests/test_yaml_config_loader.py::test_load_multiple_configs_integration PASSED                                                                      [ 97%]
tests/test_yaml_config_loader.py::test_memory_usage_stress
---------------------------------------------------------------------- live log call ----------------------------------------------------------------------
INFO     tests.test_yaml_config_loader:test_yaml_config_loader.py:503 Memory usage: Before=136.45MB, After=170.22MB, Diff=33.78MB
INFO     tests.test_yaml_config_loader:test_yaml_config_loader.py:506 Time to load large file: 94.885 seconds
PASSED                                                                                                                                               [ 98%]
tests/test_yaml_config_loader.py::test_repeated_loads_stress
---------------------------------------------------------------------- live log call ----------------------------------------------------------------------
INFO     tests.test_yaml_config_loader:test_yaml_config_loader.py:530 Completed 1000 load operations in 0.817 seconds
INFO     tests.test_yaml_config_loader:test_yaml_config_loader.py:531 Average time per load: 0.817 ms
PASSED                                                                                                                                               [ 99%]
tests/test_yaml_config_loader.py::test_concurrent_access_simulation_stress
---------------------------------------------------------------------- live log call ----------------------------------------------------------------------
INFO     tests.test_yaml_config_loader:test_yaml_config_loader.py:568 Completed 1000 load operations across 20 threads
INFO     tests.test_yaml_config_loader:test_yaml_config_loader.py:571 Total time: 1.429 seconds
INFO     tests.test_yaml_config_loader:test_yaml_config_loader.py:572 Average time per operation: 1.429 ms
PASSED                                                                                                                                               [100%]

======================================================= 91 passed, 20 skipped in 101.29s (0:01:41) ========================================================
```
