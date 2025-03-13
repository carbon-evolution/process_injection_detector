/**
 * test_injection_fixed.c - Harmless DLL for testing process injection detection
 * 
 * This DLL simply displays a message box when successfully injected into a process.
 * It can be used to safely test process injection detection capabilities.
 * 
 * Compile with: cl.exe /LD test_injection_fixed.c user32.lib
 * Or with MinGW: gcc -shared -o test_injection_fixed.dll test_injection_fixed.c -luser32
 */

#include <windows.h>

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        // Create a very obvious indication that injection succeeded
        MessageBox(NULL,
                  "DLL Injection Test Successful\nThis is a harmless test DLL for the Process Injection Detector",
                  "Process Injection Detector - Test",
                  MB_OK | MB_ICONINFORMATION);
    }
    return TRUE;
} 