#include <stdio.h>
#include <stdint.h>

#define REG_FILE_BASE_ADDR 0x00000000

#include "test_cdriver.h"

int main(void)
{
    int retval = 0;
    printf("Running test application\n\n");
    
    // Check addresses
    printf("Checking address values\n");
    printf("REG_TEST_REGISTER_ADDR = 0x%08X\n", REG_TEST_REGISTER_ADDR);
    if (REG_TEST_REGISTER_ADDR != 0) { printf("FAILED!\n"); retval++; }
    printf("REG_SCRATCH_REGISTER_ADDR = 0x%08X\n", REG_SCRATCH_REGISTER_ADDR);
    if (REG_SCRATCH_REGISTER_ADDR != 4) { printf("FAILED!\n"); retval++; }
    printf("REG_REGISTER_WITH_FIELDS_ADDR = 0x%08X\n", REG_FILE_BASE_ADDR);
    if (REG_REGISTER_WITH_FIELDS_ADDR != 64) { printf("FAILED!\n"); retval++; }

    printf("\nTesting set values\n");
    uint32_t val;
    val = REG_REGISTER_WITH_FIELDS_SET_REG4((1<<5)-1);
    printf("REG_REGISTER_WITH_FIELDS_SET_REG4((1<<5)-1) = 0x%08X\n", val);
    if (val != 0x0000000F) { printf("FAILED!\n"); retval++; }
    val = REG_REGISTER_WITH_FIELDS_SET_REG8((1<<8)-1);
    printf("REG_REGISTER_WITH_FIELDS_SET_REG8((1<<8)-1) = 0x%08X\n", val);
    if (val != 0x00000FF0) { printf("FAILED!\n"); retval++; }
    val = REG_REGISTER_WITH_FIELDS_SET_REG3((1<<3)-1);
    printf("REG_REGISTER_WITH_FIELDS_SET_REG3((1<<3)-1) = 0x%08X\n", val);
    if (val != 0x00007000) { printf("FAILED!\n"); retval++; }

    printf("\nTesting get values\n");
    val = REG_REGISTER_WITH_FIELDS_GET_REG4(0xFFFFFFFF);
    printf("REG_REGISTER_WITH_FIELDS_GET_REG4(0xFFFFFFFF) = 0x%08X\n", val);
    if (val != 0x0000000F) { printf("FAILED!\n"); retval++; }
    val = REG_REGISTER_WITH_FIELDS_GET_REG8(0xFFFFFFFF);
    printf("REG_REGISTER_WITH_FIELDS_GET_REG8(0xFFFFFFFF) = 0x%08X\n", val);
    if (val != 0x000000FF) { printf("FAILED!\n"); retval++; }
    val = REG_REGISTER_WITH_FIELDS_GET_REG3(0xFFFFFFFF);
    printf("REG_REGISTER_WITH_FIELDS_GET_REG3(0xFFFFFFFF) = 0x%08X\n", val);
    if (val != 0x00000007) { printf("FAILED!\n"); retval++; }

    printf("\nTesting complete!\n");
    printf("Errors: %d\n", retval);
    return retval;
}