// Use message:
// sudo ./read_voltage coreid voltage_waveform_coreid.csv,for example:
// sudo ./read_voltage 0 voltage_waveform_core0.csv
// time count version: time sudo ./read_core_voltage 1 voltage_waveform_core1.csv

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdint.h>
#include <sched.h>
#include <string.h>
#include <sys/mman.h>

// MSR address and field range
#define MSR_OC_MBOX 0x150 // Overclocking mailbox

#define MSR_IA32_PERF_STATUS 0x198 // Read Address of performance status
#define MSR_IA32_PERF_CTL 0x199 // Write Address of performance status


#define MSR_IA32_PERF_STATUS_VOLTAGE_FIELD_HIGH 47
#define MSR_IA32_PERF_STATUS_VOLTAGE_FIELD_LOW 32

// 1 for (1/1024 V)
#define MAILBOX_OFFSET_CORE_VOLT(offset) (0x8000001100000000 ^ (((uint64_t)(offset) & 0x7ff) << 21))
#define MAILBOX_SET_CORE_VOLT(value) (0x8000001100000000 ^ (((uint64_t)(value) & 0xfff) << 8))

// utils
#define MV_TO_MBOX(value) ((int)((value) * 1.024))
#define STATUS_TO_V(value) ((double)((value)*1./8192))

// Extract specific bits from a 64-bit value
#define EXTRACT_BITS(value, high, low)  ((value) >> (low)) & ((1ULL << ((high) - (low) + 1)) - 1)
uint64_t extract_bits(uint64_t value, int high, int low);


// Function to read an MSR register
uint64_t read_msr(int core_id, uint32_t msr_address);

// Function to write an MSR register
void write_msr(int core_id, uint32_t msr_address, uint64_t val);
