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
        """
        Setup input and output systems for the gui as well as variables that
        save important information.

        Variables relevant outside this function (anything besides static labels):
        == For getting input:
        - self.attribute_score_input: textbox input for attribute scores
        - self.prof_textbox: input for proficiency bonus
        == For giving output:
        - self.attribute_mod_labels[i]: labels giving attribute modifiers
        - self.save_mod_labels: labels for save modifiers
        == Variables for useful numbers:
        - self.attribute_mods: integer list of modifiers for attributes
        - self.proficiency: integer proficiency bonus
        - self.save_prof: bool array indicating which saves have proficiency
        - self.save_mods: integer array of actual saving throw modifiers
        """

        # ---------------------------------------------------------------------
        # Attribute Section
        # ---------------------------------------------------------------------
        # Setup attribute buttons
        self.attribute_names = ['Strength', 'Dexterity', 'Constitution',
                                'Intelligence', 'Wisdom', 'Charisma']

        self.attribute_mod_labels = []
        self.attribute_mods = [0, 0, 0, 0, 0, 0]
        self.attribute_score_input = []

        for i, name in enumerate(self.attribute_names):
            # Create button for rolling
            btn = QtWidgets.QPushButton(name, self)

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
            # The partial function is just so I can pass a number in. There is
            # probably a more clear way to do this.
            btn.clicked.connect(partial(self.attribute_roll, i))

            # Connect the text box to the function which calculates and changes
            # the modifier label
            textbox.editingFinished.connect(partial(self.set_modifier, i))

        # ---------------------------------------------------------------------
        # Proficiency Section
        # ---------------------------------------------------------------------
        # Setup proficiency modifier input
        self.proficiency = 2
        self.prof_textbox = QtWidgets.QLineEdit(self)
        self.prof_textbox.setText(str(self.proficiency))
        prof_label = QtWidgets.QLabel('Proficiency Bonus', self)

        # Move and resize proficiency things
        prof_label.resize(125, 20)
        prof_label.move(180, 20)

        self.prof_textbox.resize(26, 20)
        self.prof_textbox.move(150, 20)

        # Connect textbox to self.proficiency
        self.prof_textbox.editingFinished.connect(self.set_prof)

        # ---------------------------------------------------------------------
        # Saving Throw Section
        # ---------------------------------------------------------------------
        self.save_mod_labels = []
        self.save_mods = [0]*6
        self.save_prof = [False]*6  # all buttons start off, flip when toggled

        for i, name in enumerate(self.attribute_names):
            # Create button for rolling
            btn = QtWidgets.QPushButton(name, self)

            # create label showing modifier for this save
            label = QtWidgets.QLabel('+0', self)
            self.save_mod_labels.append(label)

            # create checkbox button for this save
            checkbox = QtWidgets.QCheckBox(self)

            # Move and resize everything
            label.resize(26, 30)
            label.move(175, i*35+50)

            checkbox.resize(26, 30)
            checkbox.move(155, i*35+50)

            btn.resize(100, 30)
            btn.move(200, i*35+50)

            # Connect checkbox button to proficiency
            checkbox.stateChanged.connect(partial(self.set_save_prof, i))

            # Connect the saving roll button to the saving roll function
            btn.clicked.connect(partial(self.saving_roll, i))

        # ---------------------------------------------------------------------
        # Skills Section
        # ---------------------------------------------------------------------

        self.show()

    def attribute_roll(self, i):
        mod = self.attribute_mods[i]

        print('Rolling for {}'.format(self.attribute_names[i]))

        r1 = d(20)
        r2 = d(20)

        print('Rolls:', r1, r2)
        print('Mod:', mod)

        print(r1+mod, r2+mod)

    def saving_roll(self, i):
        mod = self.save_mods[i]

        print('{} saving roll'.format(self.attribute_names[i]))

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

            self.recalculate()

    def set_prof(self):
        textbox_value = self.prof_textbox.text()

        if textbox_value.isdigit():
            prof = int(textbox_value)
            self.proficiency = prof

            self.recalculate()

    def set_save_prof(self, i):
        self.save_prof[i] = not self.save_prof[i]
        self.recalculate()

    def recalculate(self):
        """
        Recalculates modifiers for saves and skills
        """
        # Saves
        for i in range(6):
            mod = self.attribute_mods[i]
            if self.save_prof[i]:
                mod += self.proficiency
            self.save_mods[i] = mod

        self.fix_labels()

    def fix_labels(self):
        for i in range(6):
            # attributes
            mod = self.attribute_mods[i]
            if mod >= 0:
                s = '+'+str(mod)
            else:
                s = str(mod)
            self.attribute_mod_labels[i].setText(s)

            # saves
            mod = self.save_mods[i]
            if mod >= 0:
                s = '+'+str(mod)
            else:
                s = str(mod)
            self.save_mod_labels[i].setText(s)


def main():
    app = QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())


main()
