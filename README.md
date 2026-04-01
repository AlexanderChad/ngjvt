# ngjvt - NVIDIA GPU Junction/VRAM Temperature Library

Минималистичная библиотека под Linux на языке C для чтения температуры `junction/hotspot` (горячей точки) графического процессора и `видеопамяти`. Создана как вспомогательная к NVML (`pynvml`, я использую `ngjvt` с python), которая не возвращает эти температуры для потребительских графических процессоров.  
A minimalistic C library for Linux for reading GPU `junction/hotspot` and `vram` temperatures. It's designed as a companion to NVML (`pynvml`, I use `ngjvt` with Python), which doesn't return these temperatures for consumer GPUs.  

Протестировано на виртуальной машине `Debian 12` с использованием сквозной передачи графического процессора из `Proxmox 8.4`.  
Tested on `Debian 12` VM with GPU passthrough from `Proxmox 8.4`.  

Внимание! Методы получения температур основаны на обратном проектировании драйвера графического процессора NVIDIA для Linux и могут работать некорректно с некоторыми драйверами или видеокартами, а также могут перестать работать с более новыми версиями драйверов.  
Warning! The temperature retrieval methods are based on reverse engineering of the NVIDIA GPU driver for Linux and may not work correctly with some drivers or graphics cards, and may no longer work with newer driver versions.   

## Files

| File | Description |
|------|-------------|
| `ngjvt.c` | Реализация на языке Cи / C implementation |
| `ngjvt.so` | Библиотека на Cи (после компиляции) / C library (after compilation) |
| `pyngjvt.py` | Реализация на Python (компиляция не требуется) / Python implementation (no compilation needed) |
| `test_ngjvt.py` | Тестовый скрипт с выбором реализации / Test script with implementation selection |

## Compile ( C )

```bash
gcc -shared -fPIC -O3 -o ngjvt.so ngjvt.c
```

## Test

```bash
sudo python3 test_ngjvt.py
```

Скрипт предложит выбрать реализацию на языке C или Python.  
The script will prompt to select C or Python implementation.  

Пример вывода / example output:
```
ngjvt v1.0
0x0000000082000000 j=79°C vram=88°C
0x0000000084000000 j=54°C vram= 0°C
```

В этом примере / in this example:
- First line: RTX 3090 (both junction and VRAM temps available)
- Second line: RTX 2080 Ti (junction works, VRAM not supported)

## Requirements

- **Root privileges** - required for `/dev/mem` access
- **Kernel parameter** `iomem=relaxed`, disabled Secure Boot

To add kernel parameter:
```bash
sudo nano /etc/default/grub
# Add to GRUB_CMDLINE_LINUX_DEFAULT:
GRUB_CMDLINE_LINUX_DEFAULT="quiet iomem=relaxed"
sudo update-grub
sudo reboot
```

To disable Secure Boot:
```bash
sudo mokutil --disable-validation
sudo reboot
```

## API

```c
int ngjvt_init(void);                      // Initialize, returns 0 on success
int ngjvt_get_junction_temp(uint64_t bar);  // Get junction temp, -1 on error
int ngjvt_get_vram_temp(uint64_t bar);      // Get VRAM temp, -1 on error
void ngjvt_shutdown(void);                  // Cleanup
const char* ngjvt_version(void);            // Returns lib version
```

## Supported GPUs

**Works (should):**
- RTX 4090, 4080, 4070 Ti, 4070, 4060 Ti, 4060 (Ada)
- RTX 3090, 3080 Ti, 3080 (GA102)
- RTX A2000, A4500, A5000, A6000
- L4, L40S, A10
- RTX 2080 Ti (junction only)

**Not working:**
- RTX 3070, 3060 Ti, 3060 (GA104/GA106) - different register layout
- Any other card not listed above

## Credits

- [olealgoritme/gddr6](https://github.com/olealgoritme/gddr6) - pioneering the method to access undocumented GPU registers
- [jjziets/gddr6_temps](https://github.com/jjziets/gddr6_temps) - showing how to get VRAM and Junction temps
- [ThomasBaruzier/gddr6-core-junction-vram-temps](https://github.com/ThomasBaruzier/gddr6-core-junction-vram-temps) - a generalized code for obtaining temperatures
