import imgui

def resize(self, width: int, height: int):
    # monitor = glfw.get_primary_monitor()
    # print(glfw.get_window_size(self.wnd._window))
    # print(glfw.get_framebuffer_size(self.wnd._window))
    # print(self.wnd.pixel_ratio)
    # print(glfw.get_window_content_scale(self.wnd._window))
    # print()

    self.imgui.resize(width, height)
    self.camera.projection.update(aspect_ratio=self.wnd.aspect_ratio)

def key_event(self, key, action, modifiers):
    self.imgui.key_event(key, action, modifiers)

    self._shift = modifiers.shift

    if action == self.wnd.keys.ACTION_PRESS:
        if key == self.wnd.keys.SPACE:
            self.pause = not self.pause

def mouse_position_event(self, x, y, dx, dy):
    self.imgui.mouse_position_event(x, y, dx, dy)

def mouse_drag_event(self, x, y, dx, dy):
    self.imgui.mouse_drag_event(x, y, dx, dy)

    if imgui.get_io().want_capture_mouse: return

    self.camera.rot_state(dx, dy)

def mouse_scroll_event(self, x_offset, y_offset):
    self.imgui.mouse_scroll_event(x_offset, y_offset)

    if imgui.get_io().want_capture_mouse: return

    if self._shift:
        y_offset *= 4
    self.camera.zoom_state(y_offset)

def mouse_press_event(self, x, y, button):
    self.imgui.mouse_press_event(x, y, button)

def mouse_release_event(self, x: int, y: int, button: int):
    self.imgui.mouse_release_event(x, y, button)

def unicode_char_entered(self, char):
    self.imgui.unicode_char_entered(char)
