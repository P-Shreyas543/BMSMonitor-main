import tkinter as tk

from bms_monitor import BMSMonitorApp


def main():
    root = tk.Tk()
    BMSMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
