#/bin/bash

if [ "$#" != "1"  ];
then
    echo "Usage:"
    echo "    copy_and_compile.sh main_script.py"
    exit 1
fi

main_script=workshop/programs/$1
if ! [ -f $main_script ];
then
    echo "Couldn't find $main_script in working directory"
    exit 1
fi

set -e

echo "Copying Workshop firmware and scripts to container..."
mkdir /micropython/ports/rp2/modules/computer
cp -r workshop/computer/*.py /micropython/ports/rp2/modules/computer

# create /main.py
echo "Creating main.py..."
cp $main_script /micropython/ports/rp2/modules/main.py

echo "Compiling micropython and firmware modules..."
cd /micropython/ports/rp2
make

echo "Moving firmware file to build directory"
mv build-RPI_PICO/firmware.uf2 /workshop/uf2_build/workshop_firmware_$1.uf2
