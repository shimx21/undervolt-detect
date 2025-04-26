#include "rwmsr.h"
#include <time.h>

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

    // Set CPU affinity to the specified core
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(core_id, &cpuset);

    if (sched_setaffinity(0, sizeof(cpu_set_t), &cpuset) == -1)
    {
        fprintf(flog, "Error setting CPU affinity");
        return -1;
    }

    fprintf(flog, "Monitoring voltage on core %d.", core_id);

    clock_gettime(CLOCK_REALTIME, &st);

    for (int i = 0; i < read_num; i++)
    {
        do clock_gettime(CLOCK_REALTIME, &rt);
        while ((rt.tv_sec - st.tv_sec)*1000 + (rt.tv_nsec - st.tv_nsec) < i * interval);
        uint64_t msr_value = read_msr(core_id, MSR_IA32_PERF_STATUS);
        uint64_t voltage_value = extract_bits(
            msr_value,
            MSR_IA32_PERF_STATUS_VOLTAGE_FIELD_HIGH,
            MSR_IA32_PERF_STATUS_VOLTAGE_FIELD_LOW
        );
        fprintf(fout, "%lu\n", voltage_value); // Write to fout
    }

    clock_gettime(CLOCK_REALTIME, &et);

    fprintf(flog, "Time used per read (ns): %lf\n", (et.tv_sec-st.tv_sec)*(1e8/read_num)+(et.tv_nsec - st.tv_nsec)*1./read_num);

    fprintf(flog, "Data collection complete.\n");
    fclose(fout);
    fclose(flog);
    return read_num;
}
