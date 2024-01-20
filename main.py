from src.boids import MyWindow
import moderngl_window

if __name__ == "__main__":
    # import sys
    # import os
    # if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    #     os.chdir(sys._MEIPASS)

    # MyWindow.run(config)
    moderngl_window.run_window_config(config_cls=MyWindow, args=["-wnd", "glfw"])
