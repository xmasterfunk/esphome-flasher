# This GUI is a fork of the brilliant https://github.com/marcelstoer/nodemcu-pyflasher

import sys
import threading

import wx
import wx.adv
from wx.lib.embeddedimage import PyEmbeddedImage
import wx.lib.inspection
import wx.lib.mixins.inspection

from esphomeflasher.helpers import list_serial_ports


# See discussion at http://stackoverflow.com/q/41101897/131929
class RedirectText:
    def __init__(self, text_ctrl):
        self._out = text_ctrl

    def write(self, string):
        if string.startswith("\r"):
            # carriage return -> remove last line i.e. reset position to start of last line
            current_value = self._out.GetValue()
            last_newline = current_value.rfind("\n")
            new_value = current_value[:last_newline + 1]  # preserve \n
            new_value += string[1:]  # chop off leading \r
            wx.CallAfter(self._out.SetValue, new_value)
        else:
            wx.CallAfter(self._out.AppendText, string)

    def flush(self):
        pass


class FlashingThread(threading.Thread):
    def __init__(self, parent, firmware, port):
        threading.Thread.__init__(self)
        self.daemon = True
        self._parent = parent
        self._firmware = firmware
        self._port = port

    def run(self):
        try:
            from esphomeflasher.__main__ import run_esphomeflasher

            argv = ['esphomeflasher', '--port', self._port, self._firmware]
            run_esphomeflasher(argv)
        except Exception as e:
            print("Unexpected error: {}".format(e))
            raise


class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, size=(700, 650),
                          style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)

        self._firmware = None
        self._port = None

        self._build_status_bar()
        self._build_menu_bar()
        self._init_ui()

        sys.stdout = RedirectText(self.console_ctrl)

        self.SetMinSize((640, 480))
        self.Centre(wx.BOTH)
        self.Show(True)

    def _init_ui(self):
        def on_reload(event):
            self.choice.SetItems(self._get_serial_ports())

        def on_clicked(event):
            self.console_ctrl.SetValue("")
            worker = FlashingThread(self, self._firmware, self._port)
            worker.start()

        def on_select_port(event):
            choice = event.GetEventObject()
            self._port = choice.GetString(choice.GetSelection())

        def on_pick_file(event):
            self._firmware = event.GetPath().replace("'", "")

        panel = wx.Panel(self)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        fgs = wx.FlexGridSizer(7, 2, 10, 10)

        self.choice = wx.Choice(panel, choices=self._get_serial_ports())
        self.choice.Bind(wx.EVT_CHOICE, on_select_port)
        bmp = Reload.GetBitmap()
        reload_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp,
                                        size=(bmp.GetWidth() + 7, bmp.GetHeight() + 7))
        reload_button.Bind(wx.EVT_BUTTON, on_reload)
        reload_button.SetToolTip("Reload serial device list")

        file_picker = wx.FilePickerCtrl(panel, style=wx.FLP_USE_TEXTCTRL)
        file_picker.Bind(wx.EVT_FILEPICKER_CHANGED, on_pick_file)

        serial_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        serial_boxsizer.Add(self.choice, 1, wx.EXPAND)
        serial_boxsizer.AddStretchSpacer(0)
        serial_boxsizer.Add(reload_button, 0, wx.ALIGN_RIGHT, 20)

        button = wx.Button(panel, -1, "Flash ESP")
        button.Bind(wx.EVT_BUTTON, on_clicked)

        self.console_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.console_ctrl.SetFont(
            wx.Font(13, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.console_ctrl.SetBackgroundColour(wx.BLACK)
        self.console_ctrl.SetForegroundColour(wx.RED)
        self.console_ctrl.SetDefaultStyle(wx.TextAttr(wx.RED))

        port_label = wx.StaticText(panel, label="Serial port")
        file_label = wx.StaticText(panel, label="Firmware")

        console_label = wx.StaticText(panel, label="Console")

        fgs.AddMany([
            port_label, (serial_boxsizer, 1, wx.EXPAND),
            file_label, (file_picker, 1, wx.EXPAND),
            (wx.StaticText(panel, label="")), (button, 1, wx.EXPAND),
            (console_label, 1, wx.EXPAND), (self.console_ctrl, 1, wx.EXPAND)])
        fgs.AddGrowableRow(3, 1)
        fgs.AddGrowableCol(1, 1)
        hbox.Add(fgs, proportion=2, flag=wx.ALL | wx.EXPAND, border=15)
        panel.SetSizer(hbox)

    def _get_serial_ports(self):
        ports = []
        for port, desc in list_serial_ports():
            ports.append(port)
        if not self._port and ports:
            self._port = ports[0]
        if not ports:
            ports.append("")
        return ports

    def _build_status_bar(self):
        self.statusBar = self.CreateStatusBar(2, wx.STB_SIZEGRIP)
        self.statusBar.SetStatusWidths([-2, -1])
        status_text = "Welcome to esphomeflasher (based on PyFlasher)"
        self.statusBar.SetStatusText(status_text, 0)

    def _build_menu_bar(self):
        self.menuBar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        wx.App.SetMacExitMenuItemId(wx.ID_EXIT)
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl-Q", "Exit esphomeflasher")
        exit_item.SetBitmap(Exit.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_exit_app, exit_item)
        self.menuBar.Append(file_menu, "&File")

        # Help menu
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ABOUT, '&About esphomeflasher', 'About')
        self.menuBar.Append(help_menu, '&Help')

        self.SetMenuBar(self.menuBar)

    # Menu methods
    def _on_exit_app(self, event):
        self.Close(True)

    def log_message(self, message):
        self.console_ctrl.AppendText(message)


class App(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def OnInit(self):
        wx.SystemOptions.SetOption("mac.window-plain-transition", 1)
        self.SetAppName("esphomeflasher")

        frame = MainFrame(None, "esphomeflasher")
        frame.Show()

        return True


Exit = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABGdBTUEAAK/INwWK6QAAABl0"
    "RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAN1SURBVHjaYvz//z8DJQAggFhA"
    "xEpGRgaQMX+B+A8DgwYLM1M+r4K8P4+8vMi/P38Y3j18+O7Fs+fbvv7+0w9Uc/kHVG070HKA"
    "AGJBNg0omC5jZtynnpfHJeHkzPDmxQuGf6/eMIj+/yP+9MD+xFPrN8Reu3W3Gqi0D2IXAwNA"
    "AIEN+A/hpWuEBMwwmj6TgUVEjOHTo0cM9y9dZfj76ycDCysrg4K5FYMUvyAL7+pVnYfOXwJp"
    "6wIRAAHECAqDJYyMWpLmpmftN2/mYBEVZ3h38SLD9wcPGP6LioIN/7Z+PQM3UB3vv/8MXB/f"
    "MSzdvv3vpecvzfr+/z8HEEBMYFMYGXM0iwrAmu+sXcvw4OxZhqenTjEwAv3P9OsXw+unTxne"
    "6Osz3Ll3l+HvyzcMVlLSzMBwqgTpBQggsAG8MuKB4r9eM7zfv5PhHxMzg4qLCwPD0ycMDL9/"
    "MzD+/cvw/8kTBgUbGwbB1DSGe1cuMbD8+8EgwMPjCtILEEDgMOCSkhT+t20Nw4v7nxkkNuxm"
    "eLNmFYO0sCgDCwcHAwMzM4Pkl68MLzs7GGS6uhmOCwgxcD2+x8DLysID0gsQQGAD/gH99vPL"
    "dwZGDjaG/0An/z19goHp/z+Gn9dvgoP4/7dPDD9OnGD4+/0bA5uCAsPPW8DA5eACxxxAAIEN"
    "+PDuw/ufirJizE9fMzALCjD8efOO4dHObQx/d29k+PObgeHr268MQta2DCw8fAz/X75k+M/I"
    "xPDh1+9vIL0AAQQOg9dPX2x7w8TDwPL2FcOvI8cYxFs7GFjFpRl+PP/K8O3NVwZuIREGpe5u"
    "hp83rjF8u3iO4RsnO8OzHz8PgvQCBBA4GrsZGfUUtNXPWiuLsny59YxBch3Qdl4uhq/rNzP8"
    "BwYin58PAysbG8MFLy+Gnw9uM5xkYPp38fNX22X//x8DCCAmqD8u3bh6s+Lssy8MrCLcDC/8"
    "3Rl+LVvOwG1syMBrYcbwfetmhmsOdgy/795iuMXEwnDh89c2oJ7jIL0AAQR2wQRgXvgKNAfo"
    "qRIlJfk2NR42Rj5gEmb5+4/h35+/DJ+/fmd4DUyNN4B+v/DlWwcwcTWzA9PXQqBegACCGwAK"
    "ERD+zsBgwszOXirEwe7OzvCP5y/QCx/+/v/26vfv/R///O0GOvkII1AdKxCDDAAIIEZKszNA"
    "gAEA1sFjF+2KokIAAAAASUVORK5CYII=")

Reload = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABGdBTUEAALGOfPtRkwAAACBj"
    "SFJNAAB6JQAAgIMAAPn/AACA6AAAdTAAAOpgAAA6lwAAF2+XqZnUAAAABmJLR0QA/wD/AP+g"
    "vaeTAAAACXBIWXMAAABIAAAASABGyWs+AAAACXZwQWcAAAAYAAAAGAB4TKWmAAACZUlEQVRI"
    "x7XVT4iXRRgH8M/8Mv9tUFgRZiBESRIhbFAo8kJ0EYoOwtJBokvTxUtBQnUokIjAoCi6+HiR"
    "CNKoU4GHOvQieygMJKRDEUiahC4UtGkb63TY+cnb6/rb3276vQwzzzPf5/9MKqW4kRj8n8s5"
    "53U55y03xEDOeRu+xe5ReqtWQDzAC3gTa3D7KP20nBrknDfhMB7vHH+Dj3AWxyPitxUZyDnv"
    "xsElPL6MT/BiRJwbaaBN6eamlH9yzmvxPp5bRibPYDIizg96pIM2pak2pSexGiLiEr7H3DIM"
    "3IMP/hNBm9It+BDzmGp6oeWcd+BIvdzFRZzGvUOnOtg6qOTrcRxP4ZVmkbxFxDQm8WVPtDMi"
    "tmIDPu7JJocpehnb8F1Tyo/XijsizmMX9teCwq1VNlvrdKFzZeOgTelOvFQPfurV5NE2pc09"
    "I/MR8TqewAxu68hmMd1RPzXAw1hXD9b3nL4bJ9qUdi0SzbF699ee6K9ObU6swoMd4Y42pYmm"
    "lNm6/91C33/RpvQG9jelzHeMnK4F7uK+ur49bNNzHeEdONSmNFH3f9R1gNdwrKZ0UeSc77fQ"
    "CCfxFqSveQA/9HTn8DM2d9I3xBk83ZQy3SNPFqb4JjwTEX9S56BN6SimjI857GtKea+ST+Cx"
    "6synETHssCuv6V5sd/UQXQur8VCb0tqmlEuYi4jPF1PsTvJGvFMjGfVPzOD5ppTPxvHkqseu"
    "Teku7MQm7MEjHfFXeLYp5ey4uRz5XLcpHbAwhH/jVbzblHJ5TG4s/aPN4BT2NKWcXA7xuBFs"
    "wS9NKRdXQr6kgeuBfwEbWdzTvan9igAAADV0RVh0Y29tbWVudABSZWZyZXNoIGZyb20gSWNv"
    "biBHYWxsZXJ5IGh0dHA6Ly9pY29uZ2FsLmNvbS/RLzdIAAAAJXRFWHRkYXRlOmNyZWF0ZQAy"
    "MDExLTA4LTIxVDE0OjAxOjU2LTA2OjAwdNJAnQAAACV0RVh0ZGF0ZTptb2RpZnkAMjAxMS0w"
    "OC0yMVQxNDowMTo1Ni0wNjowMAWP+CEAAAAASUVORK5CYII=")


def main():
    app = App(False)
    app.MainLoop()
