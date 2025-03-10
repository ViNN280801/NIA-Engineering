#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "rrg.h"

#define INPUT_BUFFER_SIZE 32

RRG_Handle g_handle; // Global handle for signal handler cleanup.

/**
 * @brief Signal handler for `Ctrl+C` (SIGINT).
 * @param sig Signal number.
 */
void handle_sigint(int sig)
{
    printf("\nCaught signal %d (Ctrl+C). Closing connection...\n", sig);
    RRG_Close(&g_handle);
    exit(0);
}

/**
 * @brief Function to dynamically scan available serial ports.
 * @return A valid serial port string (e.g., "/dev/ttyUSB0") or NULL if no active ports found.
 */
char *get_active_serial_port()
{
    static char port[32];

    FILE *fp = popen("ls /dev/ttyUSB* 2>/dev/null", "r"); // Get active USB serial devices (Linux).
    if (!fp)
    {
        printf("Error: Unable to execute system command.\n");
        return NULL;
    }

    if (fgets(port, sizeof(port), fp) != NULL)
    {
        port[strcspn(port, "\n")] = '\0'; // Remove newline character.
        pclose(fp);
        return port;
    }

    pclose(fp);
    return NULL;
}

int main()
{
    // Register signal handler for SIGINT (Ctrl+C).
    signal(SIGINT, handle_sigint);

    char *port;
    RRG_Config config;
    char input[INPUT_BUFFER_SIZE];

    printf("Scanning for active serial ports...\n");

    while (1)
    {
        port = get_active_serial_port();
        if (!port)
        {
            printf("No active serial ports found. Retrying...\n");
            sleep(2);
            continue;
        }

        config.port = port;
        config.baudrate = RRG_DEFAULT_BAUDRATE;
        config.slave_id = 1;
        config.timeout = RRG_DEFAULT_TIMEOUT_MS;

        printf("Found active port: %s\n", port);

        if (RRG_Init(&config, &g_handle) != RRG_OK)
        {
            RRG_DEBUG_GET_LAST_ERR;
            sleep(2);
            continue;
        }

        if (RRG_SetGas(&g_handle, 7) == RRG_OK)
            printf("Gas set to Helium\n");
        else
        {
            RRG_DEBUG_GET_LAST_ERR;
        }

        printf("Connected successfully to %s!\n", port);
        break;
    }

    while (1)
    {
        printf("\nEnter flow setpoint (or type 'exit' to quit): ");
        fgets(input, sizeof(input), stdin);
        input[strcspn(input, "\n")] = '\0';

        if (strcmp(input, "exit") == 0)
        {
            printf("Exiting...\n");
            break;
        }

        float setpoint = atof(input);
        if (setpoint < 0)
        {
            printf("Invalid flow value. Must be a positive number.\n");
            continue;
        }

        // Set the flow value
        if (RRG_SetFlow(&g_handle, setpoint) == RRG_OK)
            printf("Flow successfully set to %.3f SCCM\n", setpoint);
        else
        {
            RRG_DEBUG_GET_LAST_ERR;
        }

        float cur_flow = -1.0;
        if (RRG_GetFlow(&g_handle, &cur_flow) == RRG_OK)
            printf("Current flow is: %.3f SCCM\n", cur_flow);
        else
        {
            RRG_DEBUG_GET_LAST_ERR;
        }
    }

    RRG_Close(&g_handle);
    return EXIT_SUCCESS;
}
