# Workshop Programs (Micropython)

All executable programs for the Workshop system should be in this directory.

## General Skeleton

Workshop programs should have a basic skeleton that looks like this:

```python
from computer.hardware import *

# define any necessary additional classes here

def main():
    # implement your program's main here


if __name__ == "__main__":
    main()
```

All hardware initialization, as well as the creation of all input & output objects is done
automatically when importing the `computer.hardware` module.


## Demos

The following demo programs provide basic examples of some of the Workshop computer's features:

- `demo_cv` -- reads the CV & pulse values from the inputs and copies them to the outputs
- `demo_knobs` -- reads the values of the X and Y knobs, using their values to set the LEDs
  and output CV values
- `demo_led_patterns` -- runs through a series LED patterns forever; all outputs should remain
  `0` at all times.
