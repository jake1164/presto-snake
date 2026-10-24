# Installing Presto Snake

Back to the [README](../README.md).

## Before you start

- A Pimoroni Presto with the official MicroPython firmware. See [Getting started with Presto](https://learn.pimoroni.com/article/getting-started-with-presto). Firmware downloads are on the [Presto releases page](https://github.com/pimoroni/presto/releases); the `with-filesystem` build is what the Pimoroni guide uses.
- A [Qw/ST Pad](https://shop.pimoroni.com/products/qwst-pad) and a Qw/ST cable.
- [Thonny](https://thonny.org), set to the **MicroPython (Raspberry Pi Pico)** interpreter.

The code opens I2C bus 0 (SDA pin 40, SCL pin 41) and talks to the pad at the first address in `qwstpad.ADDRESSES`, the default. If you have cut the address traces on the pad, the game will not find it.

## 1. Connect everything

1. Plug the Qw/ST Pad into the Presto's Qw/ST port with the cable.
2. Connect the Presto to your computer over USB.
3. In Thonny, press **Stop** to interrupt the launcher. You should see a `>>>` prompt. Show the file panel with **View → Files**.

## 2. Install the `qwstpad` library

Pimoroni's docs for `qwstpad` don't say that the library ships with the firmware, so install it unless `import qwstpad` already works at the `>>>` prompt. The repository's `package.json` supports `mip`. Either:

- **From Thonny's shell** (needs the Presto to be on Wi-Fi):

  ```python
  import mip
  mip.install("github:pimoroni/qwstpad-micropython")
  ```

- **From your computer** with [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) (Presto connected over USB):

  ```
  mpremote mip install github:pimoroni/qwstpad-micropython
  ```

- **Manually:** download [`src/qwstpad.py`](https://github.com/pimoroni/qwstpad-micropython/blob/main/src/qwstpad.py) and upload it to the `/lib` folder on the Presto (create it if needed).

## 3. Copy the game

Upload these to the **same folder** on the Presto, the top level (`/`):

| From this repo | Save on the Presto as |
| --- | --- |
| `src/snake.py` | `snake.py` |
| `src/level-0.txt` … `src/level-3.txt` | same names |

Or from a terminal with [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html), run from the repository's `src` folder:

```
mpremote fs cp snake.py level-0.txt level-1.txt level-2.txt level-3.txt :
mpremote reset
```

This only adds files, so the launcher's `main.py` is untouched.

The game opens `level-N.txt` by relative path, so the level files must be in the folder the program runs from. If one is missing the game prints `File not found: level-N.txt, using an empty level.` and plays with no walls.

## 4. Launch it

Reset the Presto. The launcher's carousel lists every `.py` file at the top level except `main.py` and `secrets.py`, so **Presto Snake** appears there with a joystick icon. Its name, icon and description come from the three `# NAME`, `# ICON` and `# DESC` comment lines at the top of `snake.py`, which the launcher reads. Tap the icon to start the game, then press `+` on the Qw/ST Pad to begin.

The game has no exit button. Press the Presto's reset button to return to the carousel.

To debug, open `snake.py` from the Presto in Thonny and press **Run**. Errors then show in the shell.

> The launcher behaviour above is taken from the launcher source in the [Presto repository](https://github.com/pimoroni/presto/blob/main/examples/main.py). It hasn't been confirmed on a device running this game.

## Troubleshooting

| Problem | Try |
| --- | --- |
| `ImportError: no module named 'qwstpad'` | Install the library (step 2). Confirm it is on the Presto in `/lib` or at the top level. |
| `OSError` / `[Errno 19] ENODEV` on startup, or the pad isn't detected | Check the Qw/ST cable and that it is seated in the Qw/ST port on both ends. Make sure the pad's I2C address hasn't been changed. |
| `ImportError` for `presto`, or `Presto` is not found | Wrong firmware. Install the official Presto MicroPython build from the [releases page](https://github.com/pimoroni/presto/releases). |
| `File not found: level-N.txt` | Upload all four level files next to the game file. |
| Presto Snake isn't in the carousel | Check that `snake.py` is at the top level of the filesystem (not in a folder) and that the first three lines are the `# NAME`/`# ICON`/`# DESC` comments. Reset the Presto. |
| Thonny can't connect or upload while the launcher is running | Press Thonny's **Stop** first, or enable *Tools → Options → Interpreter → Interrupt working program on connect*. |
