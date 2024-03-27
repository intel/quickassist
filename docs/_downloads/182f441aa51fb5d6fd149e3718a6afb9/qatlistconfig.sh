 #!/bin/bash

printf "%-13s | %-5s | %-12s | %-12s | %-10s\n"  "VFIO GROUP" "NODE"   \
"PF BDF" "VF BDF" "SERVICES"
echo "--------------------------------------------------------------"

for vfio_group in /dev/vfio/*; do
    if [ $vfio_group = "/dev/vfio/vfio" ]; then
        continue
    fi
    if [ $vfio_group = "/dev/vfio/devices" ]; then
        continue
    fi

    group=${vfio_group##*/}
    # assume one bdf per iommu group
    bdf=$(ls /sys/kernel/iommu_groups/$group/devices/)
    vendor=$(cat /sys/kernel/iommu_groups/$group/devices/$bdf/vendor)
    node=$(cat /sys/kernel/iommu_groups/$group/devices/$bdf/numa_node)
    did=$(cat /sys/kernel/iommu_groups/$group/devices/$bdf/device)

    if [ "$vendor" != "0x8086" ]; then
        continue
    fi

    if [ "$did" != "0x4941" ] && [ "$did" != "0x4943" ] && [ "$did" != "0x4947" ]; then
        continue
    fi

    regex='([a-z0-9]+):([a-z0-9]+):.*'
    [[ $bdf =~ $regex ]]
    pf_domain=${BASH_REMATCH[1]}
    pf_bus=${BASH_REMATCH[2]}
    pf_bdf="$pf_domain:$pf_bus:00.0"

    printf "%-15s %-7s %-14s %-14s %-10s\n"  "$vfio_group"  "$node"    \
    "$pf_bdf"   "$bdf"                                                 \
    "$(cat /sys/bus/pci/devices/$pf_bdf/qat/cfg_services)"

done