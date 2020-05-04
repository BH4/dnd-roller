# from dnd_roller import Character

import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication

from functools import partial
from random import randint


def d(sides):
    value = randint(1, sides)
    return value


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        # startx, starty, width, height
        self.setGeometry(50, 50, 800, 700)
        self.setWindowTitle('Unnamed Character')
        #self.setWindowIcon(QtGui.QIcon(''))  # set icon
        self.setup()

    def setup(self):
        # Setup attribute buttons
        str_btn = QtWidgets.QPushButton('Strength', self)
        dex_btn = QtWidgets.QPushButton('Dexterity', self)
        con_btn = QtWidgets.QPushButton('Constitution', self)
        int_btn = QtWidgets.QPushButton('Intelligence', self)
        wis_btn = QtWidgets.QPushButton('Wisdom', self)
        cha_btn = QtWidgets.QPushButton('Charisma', self)

        self.attribute_btns = [str_btn, dex_btn, con_btn, int_btn, wis_btn, cha_btn]
        self.attribute_mod_labels = []
        self.attribute_mods = [0, 0, 0, 0, 0, 0]
        self.attribute_score_input = []

        for i, btn in enumerate(self.attribute_btns):
            # Create a text box for the attribute score
            textbox = QtWidgets.QLineEdit(self)
            textbox.setText('10')
            self.attribute_score_input.append(textbox)

            # Create a label for the modifier
            label = QtWidgets.QLabel('+0', self)
            self.attribute_mod_labels.append(label)

            # Move and resize everything
            label.resize(39, 20)
            label.move(10+50-26//2, i*100+80)

            textbox.resize(26, 20)
            textbox.move(10+50-26//2, i*100+100)

            btn.resize(100, 30)
            btn.move(10, i*100+50)

            # Connect the button to the roll function
            # The lambda is just so I can pass a number in. There is probably a
            # more clear way to do this.
            btn.clicked.connect(partial(self.attribute_roll, i))

            # Connect the text box to the function which calculates and changes
            # the modifier label
            textbox.editingFinished.connect(partial(self.set_modifier, i))

        self.show()

    def attribute_roll(self, i):
        mod = self.attribute_mods[i]

        r1 = d(20)
        r2 = d(20)

        print('Rolls:', r1, r2)
        print('Mod:', mod)

        print(r1+mod, r2+mod)

    def set_modifier(self, i):
        textbox_value = self.attribute_score_input[i].text()

        if textbox_value.isdigit():
            score = int(textbox_value)
            mod = int(score//2)-5

            self.attribute_mods[i] = mod

            if mod >= 0:
                s = '+'+str(mod)
            else:
                s = str(mod)

            self.attribute_mod_labels[i].setText(s)


def main():
    app = QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())


main()
