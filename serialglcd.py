import serial
# import demoport   # test module...


class SerialGLCD:
    """
    This class provides some useful functionality to control Sparkfun Graphical LCD with Graphic LCD Backpack.
    """
    def __init__(self, port, baudrate=115200, lengthpixels=128, heightpixels=64):
        """
        Initialize serial LCD instance.
        :param port: Serial port name (serial arg)
        :param baudrate: Serial baudrate (serial arg)
        :param lengthpixels: Number of pixels in length
        :param heightpixels: Number of pixels in height
        """
        self.__lcdport = serial.Serial(port, baudrate)
        # demoport.DemoPort(port, baudrate, lengthpixels, heightpixels)
        if baudrate != 115200:
            self.setbaudrate(baudrate)
        self.__length = lengthpixels - 1
        self.__charlengthlimit = lengthpixels / 6   # Character length is 6 pixels
        self.__height = heightpixels - 1
        self.__charheightlimit = heightpixels / 8   # Character height is 8 pixels
        self.__cursor = (0, 0)

    @staticmethod
    def __textpixelcount(text):
        return len(text) * 6

    def __writecommand(self, command, *data):
        """
        Sends given command to the LCD. Any additional arguments are sent with the given sequence.
        :param command: Command to execute
        :param data: Any additional data specified by the command. Can be ignored if command allows.
        :return: The number of bytes written.
        """
        packet = [0x7C, command]    # Control character. First byte of all packets.
        # Add remaining arguments to the packet. If empty, nothing added.
        packet.extend(data)
        return self.__lcdport.write(packet)

    def canwrite(self, text):
        """
        Checks whether the text can be written on current line.
        :param text: String to be checked (without special ASCII-coded char e.g. 'newline (n)', 'tab (t)'.
        :return: True if text can be written.
        """
        # Add number of pixels needed to cursor position.
        return self.__cursor[0] + self.__textpixelcount(text) > self.__length

    def clearscreen(self):
        """
        Clears whole screen.
        """
        self.__writecommand(0x00)

    def drawbox(self, pnt1, pnt2, erase=False):
        """
        Draws or erases a box depending on the argument 'erase'. The box starts at pnt1 and ends at pnt2.
        :param pnt1: Any sequence type containing x and y coordinates, respectively.
        :param pnt2: Any sequence type containing x and y coordinates, respectively.
        :param erase: False to erase box, True to draw.
        """
        self.__writecommand(0x0F, pnt1[0], pnt1[1], pnt2[0], pnt2[1], (0 if erase else 1))

    def get_remaining_char_count(self):
        """
        Gets the number of remaining characters on current line
        :return: int
        """
        return (self.__length - self.__cursor[0]) // 6  # floor division to ensure integer result.

    def getcursor(self):
        """
        returns current position of the cursor. WARNING: This class does not get actual position from the device. It
        calculates the position based on operations.
        :return:
        """
        return self.__cursor

    def gotoline(self, line):
        """
        Goes to the line number specified by 'line'
        :param line: A number between 1 and 8.
        """
        # Set the limits
        if line > 8:
            line = 8
        elif line < 1:
            line = 1

        y_position = 8 * line - 8   # Each character is in a 6x8 block
        self.setcursor(0, y_position)

    def setbacklight(self, brightness):
        """
        Sets brightness of the back light.
        :param brightness: A value between 0 and 100
        """
        # TODO: check limits, numbers such that x < -256, x > 256
        self.__writecommand(0x02, brightness)

    def setbaudrate(self, baudrate):
        pass

    def setcursor(self, x, y):
        """
        Sets the position of the cursor. Text written after this command begin at x, y positions.
        Raises ValueError if arguments exceed the limits of the screen.
        :param x: X point
        :param y: Y point
        """
        if x > self.__length or y > self.__height or x < 0 or y < 0:
            raise ValueError    # to ensure open-loop cursor traction etc.

        self.__writecommand(0x18, x)   # two separate commands
        self.__writecommand(0x19, y)
        self.__cursor = (x, y)

    def writetext(self, text, clear_write=False, right_justified=False):
        """
        Writes the text on LCD.
        NOTE: Any special ASCII char newline(n), tab(t), backspace(b) etc. are not checked here.
                If they are used, cursor position will be set to wrong value in this code!
        :param text: String to be written (may be modified in the function)
        """
        if clear_write:
            self.clearscreen()              # Sets cursor to (0, 63)
            self.setcursor(*self.__cursor)  # Since 'clear screen' is not called directly by the user, reset the cursor.
        # Check if the text can be written on current line.
        while self.canwrite(text):
            # If the text is long, find the last 'space char' before the length limit. This space will be split position
            # Number of characters that can be written on this line:
            maxchars = self.get_remaining_char_count()
            splitposition = text.rfind(' ', 0, maxchars)
            # Knowing split position, get first part
            firstpart = text[0:splitposition]
            self.__lcdport.write(firstpart if not right_justified else firstpart.rjust(maxchars))
            # Set the cursor to next line. Member function 'set cursor' updated both screen and 'self'
            self.setcursor(0, self.__cursor[1] - 8)
            # Update text to remaining characters
            text = text[splitposition + 1:]
        # If text can be written on current line OR text is set to remaining characters, simply write them.
        self.__lcdport.write(text if not right_justified else text.rjust(self.get_remaining_char_count()))
        # Update the cursor in 'self' (screen updates it automatically via write command).
        self.__cursor = (self.__cursor[0] + self.__textpixelcount(text), self.__cursor[1])
