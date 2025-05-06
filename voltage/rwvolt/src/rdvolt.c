#include "rwmsr.h"
#include <time.h>

void bind_core(int core_id) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(core_id, &cpuset);

    if (sched_setaffinity(0, sizeof(cpu_set_t), &cpuset) == -1) {
        perror("Error setting CPU affinity");
        exit(EXIT_FAILURE);
    }
}

int read_core_voltage(int core_id, int read_num, int interval, int fdout, int fdlog){
    struct timespec st, et, rt;
    FILE* fout = fdopen(dup(fdout), "w");
    FILE* flog = fdopen(dup(fdlog), "w");
    // Open output CSV file
    if (!fout || !flog)
    {
        fprintf(flog, "Bad File Pointer\n");
        return -1;
    }

    char msr_path[64];
    snprintf(msr_path, sizeof(msr_path), "/dev/cpu/%d/msr", core_id);
    
    int fd = open(msr_path, O_RDONLY);
    if (fd == -1)
    {
        perror("Error opening MSR file");
        exit(EXIT_FAILURE);
    }

    fprintf(flog, "Monitoring voltage on core %d.\n", core_id);
    uint64_t value;
    clock_gettime(CLOCK_REALTIME, &st);
    for (int i = 0; i < read_num; i++)
    {
        // do clock_gettime(CLOCK_REALTIME, &rt);
        // while ((rt.tv_sec - st.tv_sec)*1000 + (rt.tv_nsec - st.tv_nsec) < i * interval);
        pread(fd, &value, sizeof(value), MSR_IA32_PERF_STATUS);
        uint64_t voltage_value = EXTRACT_BITS(
            value,
            MSR_IA32_PERF_STATUS_VOLTAGE_FIELD_HIGH,
            MSR_IA32_PERF_STATUS_VOLTAGE_FIELD_LOW
        );
        fprintf(fout, "%lu\n", voltage_value); // Write to fout
    }

    clock_gettime(CLOCK_REALTIME, &et);

    // fprintf(flog, "Start time: %ld, %ld\n", st.tv_sec, st.tv_nsec);
    // fprintf(flog, "End   time: %ld, %ld\n", et.tv_sec, et.tv_nsec);
    fprintf(flog, "Time used per read (ns): %lf\n", (et.tv_sec-st.tv_sec)*(1e9/read_num)+(et.tv_nsec - st.tv_nsec)*1./read_num);

    fprintf(flog, "Data collection complete.\n");
    fclose(fout);
    fclose(flog);
    return read_num;
}
