# Micropython

Micropython is a programming language very similar to Python. It has access to different libraries,
and is intended for use in embedded devices, like the Workshop Computer.

Python is very beginner-friendly and doesn't need specialized compilers to generate executable
code; with Python you can simply execute your source-code files.

This simplicity does have disadvantages: Micropython's performance will be noticeably slower than
the equivalent program written in C or C++. CV and gate processing is easily done with Micropython,
but high-speed applications like audio generation or audio-rate CV will likely not work reliably.

## Setup

The Micropython interpreter can be installed by simply dragging the appropriate UF2 file onto
the Workshop Computer.

### Installing Micropython

Connect the Computer to your computer with a keyboard. This should mount it as a disk.

Download the micropython uf2 file from & drag

https://www.raspberrypi.com/documentation/microcontrollers/micropython.html

Drag it to the Computer. This should eject the disk. The board is now running Micropython.

[Thonny](https://thonny.org/) is sometimes useful as is
`[picotool](https://github.com/raspberrypi/picotool) info`. If you use VSCode
[MicroPico](https://marketplace.visualstudio.com/items?itemName=paulober.pico-w-go) is quite nice.

### Installing Workshop Computer Python modules

TODO: publish the core `computer` library to PyPI + use Thonny to install the package?

Once you have installed the Micropython firmware, you will need to create the filesystem for the module.
Open your file browser and create a directory called `lib` on your Workshop computer's disk. Then copy
the entire `Micropython/computer` directory into it.

Finally, choose what program you want to run from the `Micropython/programs` directory, and copy
it onto the root directory of the disk, renaming it `main.py`.

### Precompiled UF2 files

Alternatively, instead of installing the Micropython UF2 and then manually installing the Workshop
computer libraries, you can build your own UF2 file which will include everything.

See [Building UF2 Firmware Files](#building-uf2-firmare-files) below for instructions on how to
build custom UF2 files.

Once you have built your desired UF2 file, copy it onto the Workshop computer exactly as you would
[install the Micropython UF2](#installing-micropython).

## Note on Power

The CV outputs and LEDs may not work unless the Workshop computer has Eurorack power in addition
to the USB connection for programming.

## Workshop Computer Libraries

### `computer/`
Hardware interface implementation, based somewhat on [EuroPi](https://github.com/Allen-Synthesis/EuroPi).

TODO: https://docs.micropython.org/en/latest/reference/packages.html

### `programs/`

See [Programs](/Demonstrations+HelloWorlds/Micropython/programs/README.md) documentation for guidance
on writing your own Micropython programs for the Workshop computer.

## Building UF2 Firmare Files

You may use the `uf2_build/build_uf2.sh` script to generate UF2 files for all Python programs
found in the `programs` directory. This can be a long operation, but it will generate a complete
image you can copy onto your program cards for each individual program.

Alternatively, if you only want to generate a specific UF2, `cd` into the `Micropython` directory
and run
```bash
docker run -v .:/workshop workshop_buildenv my_program.py
```
where `my_program.py` is the program from the `programs` directory you want to run. For example,
to generate the `demo_cv` UF2 you should run
```bash
cd Workshop_Computer/Demonstrations+HelloWorlds/Micropython
docker run -v .:/workshop workshop_buildenv demo_cv.py
```

The generated UF2 file(s) will be located in the `uf2_build` directory and will include the name
of the main program, for example `uf2_build/workshop_firmware_demo_cv.py.uf2`.

### Installing Docker

The UF2 generator is written to use Docker containers to perform the actual compilation. You will
need to [install Docker](https://docs.docker.com/engine/install/) for your system. If you are
using Windows, you may also find it helpful to install the Windows Subsystem for Linux (WSL),
as this can integrate with Docker and gives you access to a `bash` terminal, among other
convenient development tools.
