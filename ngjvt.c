/*
 * ngjvt - NVIDIA GPU Junction/VRAM Temperature Library
 *
 * Compile:
 *   gcc -shared -fPIC -O3 -o ngjvt.so ngjvt.c
 *
 * Usage:
 *   ngjvt_init()                      - initialize (check root, open /dev/mem)
 *   ngjvt_get_junction_temp(bar)      - get junction temp, -1 on error
 *   ngjvt_get_vram_temp(bar)          - get VRAM temp, -1 on error
 *   ngjvt_shutdown()                  - cleanup
 *
 * Requires:
 *   - Root privileges (for /dev/mem access)
 *   - iomem=relaxed kernel parameter, disabled Secure Boot
 *
 * https://github.com/AlexanderChad/ngjvt
 */

#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <sys/mman.h>

#define NGJVT_OFFSET_JUNCTION  0x0002046C
#define NGJVT_OFFSET_VRAM      0x0000E2A8
#define NGJVT_PAGE_SIZE        ((size_t)sysconf(_SC_PAGE_SIZE))

static int ngjvt_initialized = 0;
static int ngjvt_mem_fd = -1;
static char ngjvt_error[256] = {0};


int ngjvt_init(void) {
    if (ngjvt_initialized) return 0;

    if (geteuid() != 0) {
        strcpy(ngjvt_error, "Root required");
        return -1;
    }

    ngjvt_mem_fd = open("/dev/mem", O_RDONLY | O_SYNC);
    if (ngjvt_mem_fd < 0) {
        snprintf(ngjvt_error, sizeof(ngjvt_error), "open(/dev/mem): %s", strerror(errno));
        return -1;
    }

    ngjvt_initialized = 1;
    return 0;
}


const char* ngjvt_get_error(void) {
    return ngjvt_error;
}


static int read_temp(uint64_t bar, uint32_t offset) {
    if (!ngjvt_initialized) return -1;

    uint64_t addr = bar + offset;
    uint64_t page = addr & ~(NGJVT_PAGE_SIZE - 1);

    void *map = mmap(NULL, NGJVT_PAGE_SIZE, PROT_READ, MAP_SHARED, ngjvt_mem_fd, (off_t)page);
    if (map == (void*)-1) return -1;

    uint32_t val = *((uint32_t*)((char*)map + (addr - page)));
    munmap(map, NGJVT_PAGE_SIZE);

    int temp = (offset == NGJVT_OFFSET_JUNCTION) ? (val >> 8) & 0xFF : (val & 0xFFF) / 0x20;
    return (temp < 127) ? temp : -1;
}


int ngjvt_get_junction_temp(uint64_t bar) {
    return read_temp(bar, NGJVT_OFFSET_JUNCTION);
}


int ngjvt_get_vram_temp(uint64_t bar) {
    return read_temp(bar, NGJVT_OFFSET_VRAM);
}


void ngjvt_shutdown(void) {
    if (!ngjvt_initialized) return;
    if (ngjvt_mem_fd >= 0) close(ngjvt_mem_fd);
    ngjvt_initialized = 0;
}


const char* ngjvt_version(void) {
    return "1.0";
}
