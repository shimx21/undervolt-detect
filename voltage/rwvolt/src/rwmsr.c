#include "rwmsr.h"

// Extract specific bits from a 64-bit value
uint64_t extract_bits(uint64_t value, int high, int low)
{
    return (value >> low) & ((1ULL << (high - low + 1)) - 1);
}

// Function to read an MSR register
uint64_t read_msr(int core_id, uint32_t msr_address)
{
    char msr_path[64];
    snprintf(msr_path, sizeof(msr_path), "/dev/cpu/%d/msr", core_id);

    int fd = open(msr_path, O_RDONLY);
    if (fd == -1)
    {
        perror("Error opening MSR file");
        exit(EXIT_FAILURE);
    }

    uint64_t value;
    if (pread(fd, &value, sizeof(value), msr_address) != sizeof(value))
    {
        perror("Error reading MSR");
        close(fd);
        exit(EXIT_FAILURE);
    }

    close(fd);
    return value;
}

// Function to write an MSR register
void write_msr(int core_id, uint32_t msr_address, uint64_t val)
{
    char msr_path[64];
    snprintf(msr_path, sizeof(msr_path), "/dev/cpu/%d/msr", core_id);

    int fd = open(msr_path, O_WRONLY);
    if (fd == -1)
    {
        perror("Error opening MSR file");
        exit(EXIT_FAILURE);
    }

    if (pwrite(fd, &val, sizeof(val), msr_address) != sizeof(val))
    {
        perror("Error writing MSR");
        close(fd);
        exit(EXIT_FAILURE);
    }

    close(fd);
}
