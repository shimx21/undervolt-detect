#include "rwmsr.h"

int offset_core_voltage(int core_id, int offset, int fdlog){
    offset = MV_TO_MBOX(offset);
    uint64_t value = MAILBOX_OFFSET_CORE_VOLT(offset);
    FILE* flog = fdopen(dup(fdlog), "w");
    uint64_t oldvolt = extract_bits(
        read_msr(core_id, MSR_IA32_PERF_STATUS),
        MSR_IA32_PERF_STATUS_VOLTAGE_FIELD_HIGH,
        MSR_IA32_PERF_STATUS_VOLTAGE_FIELD_LOW
    );
    write_msr(core_id, MSR_OC_MBOX, value);
    uint64_t newvolt = extract_bits(
        read_msr(core_id, MSR_IA32_PERF_STATUS),
        MSR_IA32_PERF_STATUS_VOLTAGE_FIELD_HIGH,
        MSR_IA32_PERF_STATUS_VOLTAGE_FIELD_LOW
    );
    fprintf(flog, "Voltage offset applied successfully.\n");
    fclose(flog);
    return offset;
}

int set_core_voltage(int core_id, int target, int fdlog){
    target = MV_TO_MBOX(target);
    uint64_t value = MAILBOX_SET_CORE_VOLT(target);
    FILE* flog = fdopen(dup(fdlog), "w");
    write_msr(core_id, MSR_OC_MBOX, value);
    fprintf(flog, "Voltage set successfully.\n");
    fclose(flog);
    return target;
}
