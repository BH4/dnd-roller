# from dnd_roller import Character

import sys
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QPushButton, QLineEdit, QLabel
from PyQt5.QtWidgets import QCheckBox, QPlainTextEdit

from PyQt5.QtWidgets import QVBoxLayout, QGridLayout

import re
from functools import partial
from random import randint


def d(sides):
    value = randint(1, sides)
    return value


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        wid = QtWidgets.QWidget(self)
        self.setCentralWidget(wid)

        # Layout setup
        outside = QGridLayout()
        wid.setLayout(outside)
        self.attribute_layout = QVBoxLayout()
        self.saves_layout = QGridLayout()
        self.skills_layout = QGridLayout()
        self.pass_percep_layout = QGridLayout()
        self.attacks_layout = QGridLayout()
        self.log_layout = QGridLayout()

        c1_size = 5
        c2 = c1_size+1
        c2_size = 3*c1_size
        c3_start = c2+c2_size+1
        c3_size = 2*c2_size
        y = 24
        outside.addLayout(self.attribute_layout,   1,    0,            y-2,    c1_size)
        outside.addLayout(self.saves_layout,       0,    c2,           y//4,   c2_size)
        outside.addLayout(self.skills_layout,      y//4, c2,           3*y//4, c2_size)
        outside.addLayout(self.pass_percep_layout, y,    0,            1,      c1_size+c2_size)
        outside.addLayout(self.attacks_layout,     0,    c3_start,     y//2,   c3_size)
        outside.addLayout(self.log_layout,         y//2, c3_start,     y//2,   c3_size)

        self.saves_layout.setVerticalSpacing(0)
        self.skills_layout.setVerticalSpacing(0)

        # startx, starty, width, height
        self.setGeometry(50, 50, 1200, 950)
        self.setWindowTitle('Unnamed Character')

        save_action = QtWidgets.QAction('&Save Character', self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Save Character')
        save_action.triggered.connect(self.save_character)

        load_action = QtWidgets.QAction('&Load Character', self)
        load_action.setShortcut('Ctrl+O')
        load_action.setStatusTip('Load Character')
        load_action.triggered.connect(self.load_character)

        self.statusBar()

        main_menu = self.menuBar()
        file_menu = main_menu.addMenu('&File')
        file_menu.addAction(save_action)
        file_menu.addAction(load_action)

        self.setup()

    def save_character(self):
        """
        In order to recreate everything we just need the attribute scores,
        the proficiency bonus, and the list of proficiencies,
        both saves and skills.
        """

        file = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Character')
        filename = file[0]
        name = filename.split('/')[-1]

        if len(name) == 0:
            return

        filename += '.txt'

        self.setWindowTitle(name)

        with open(filename, 'w') as f:
            f.write(str(self.attribute_scores)+'\n')
            f.write(str(self.proficiency)+'\n')
            f.write(str(self.save_prof)+'\n')
            f.write(str(self.skill_prof)+'\n')
            f.write(str(self.attack_list)+'\n')

    def load_character(self):
        file = QtWidgets.QFileDialog.getOpenFileName(self, 'Load Character')
        filename = file[0]
        name = filename.split('/')[-1]
        name = name[:-4]

        if len(filename) == 0:
            return

        # Close window and open a new one
        self.close()
        self = Window()

        self.setWindowTitle(name)

        with open(filename, 'r') as f:
            line = f.readline().strip()[1:-1]
            self.attribute_scores = [int(x) for x in line.split(', ')]

            line = f.readline().strip()
            self.proficiency = int(line)

            line = f.readline().strip()[1:-1]
            new_save_prof = [x == 'True' for x in line.split(', ')]

            line = f.readline().strip()[1:-1]
            new_skill_prof = [x == 'True' for x in line.split(', ')]

            # Add custom attacks back in.
            line = f.readline().strip()[2:-2]
            for attack in line.split('], ['):
                self.add_attack()
                for i, t in enumerate(attack[1:-1].split("', '")):
                    self.attack_widget_list[-1][i].setText(t)

                # Make sure to save these after entering the data
                self.save_attack(len(self.attack_list)-1)

        self.fix_textboxes_and_checkboxes(new_save_prof, new_skill_prof)

        self.recalculate()

    def setup(self):
        """
        Setup input and output systems for the gui as well as variables that
        save important information.

        Variables relevant outside this function (anything dynamic):
        == For getting input:
        - self.attribute_score_input: text box input for attribute scores
        - self.prof_textbox: input for proficiency bonus
        - self.attack_widget_list: textboxes for custom attacks

        == For giving output:
        - self.attribute_mod_labels[i]: labels giving attribute modifiers
        - self.save_mod_labels: labels for save modifiers
        - self.skill_mod_labels: labels for skill modifiers

        == Variables for useful numbers:
        - self.attribute_names: names of attributes in character sheet order
        - self.attribute_scores: most recent integer input to score
        - self.attribute_mods: integer list of modifiers for attributes
        - self.proficiency: integer proficiency bonus
        - self.save_prof: bool array indicating which saves have proficiency
        - self.save_checkbox:
        - self.save_mods: integer array of actual saving throw modifiers
        - self.skill_names: names of skills in alphabetical order
        - self.skill_types: index of relevant attribute for the skills
        - self.skill_prof: bool array indicating which skills have proficiency
        - skill_checkbox:
        - self.skill_mods: integer array of actual skill modifiers
        - self.attack_list: last acceptable input for a custom attack
        """

        # ---------------------------------------------------------------------
        # Attribute Section
        # ---------------------------------------------------------------------
        # Setup attribute buttons
        self.attribute_names = ['Strength', 'Dexterity', 'Constitution',
                                'Intelligence', 'Wisdom', 'Charisma']
        self.attribute_short = ['Str', 'Dex', 'Con', 'Int', 'Wis', 'Cha']

        self.attribute_mod_labels = []
        self.attribute_scores = [10]*6
        self.attribute_mods = [0]*6
        self.attribute_score_input = []

        for i, name in enumerate(self.attribute_names):
            # Create button for rolling
            btn = QPushButton(name, self)

            # Create a text box for the attribute score
            textbox = QLineEdit(self)
            textbox.setText('10')
            textbox.setAlignment(QtCore.Qt.AlignCenter)
            textbox.setMaximumWidth(30)
            self.attribute_score_input.append(textbox)

            # Create a label for the modifier
            label = QLabel('+0', self)
            self.attribute_mod_labels.append(label)

            self.attribute_layout.addWidget(btn)
            self.attribute_layout.addWidget(label)
            self.attribute_layout.addWidget(textbox)
            self.attribute_layout.addSpacing(30)

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
        self.prof_textbox = QLineEdit(self)
        self.prof_textbox.setText(str(self.proficiency))
        self.prof_textbox.setAlignment(QtCore.Qt.AlignCenter)
        prof_label = QLabel('Proficiency Bonus', self)

        self.prof_textbox.setMaximumWidth(20)

        # Add and resize proficiency widgets
        self.saves_layout.addWidget(prof_label, 0, 1, 1, 2)
        self.saves_layout.addWidget(self.prof_textbox, 0, 0)

        # Connect textbox to self.proficiency
        self.prof_textbox.editingFinished.connect(self.set_prof)

        # ---------------------------------------------------------------------
        # Saving Throw Section
        # ---------------------------------------------------------------------
        self.save_mod_labels = []
        self.save_mods = [0]*6
        self.save_prof = [False]*6  # all buttons start off, flip when toggled
        self.save_checkbox = []

        for i, name in enumerate(self.attribute_names):
            # Create button for rolling
            btn = QPushButton(name, self)
            btn.setMaximumSize(btn.minimumSizeHint())

            # create label showing modifier for this save
            label = QLabel('+0', self)
            label.setMaximumWidth(30)
            self.save_mod_labels.append(label)

            # create checkbox button for this save
            checkbox = QCheckBox(self)
            checkbox.setMaximumWidth(30)
            self.save_checkbox.append(checkbox)

            self.saves_layout.addWidget(checkbox, i+1, 0)
            self.saves_layout.addWidget(label, i+1, 1)
            self.saves_layout.addWidget(btn, i+1, 2)

            # Connect checkbox button to proficiency
            checkbox.stateChanged.connect(partial(self.set_save_prof, i))

            # Connect the saving roll button to the saving roll function
            btn.clicked.connect(partial(self.saving_roll, i))

        # ---------------------------------------------------------------------
        # Skills Section
        # ---------------------------------------------------------------------
        self.skill_names = ['Acrobatics', 'Animal Handling', 'Arcana',
                            'Athletics', 'Deception', 'History', 'Insight',
                            'Intimidation', 'Investigation', 'Medicine',
                            'Nature', 'Perception', 'Performance',
                            'Persuasion', 'Religion', 'Sleight of Hand',
                            'Stealth', 'Survival']
        self.skill_type = [1, 4, 3, 0, 5, 3, 4, 5, 3,
                           4, 3, 4, 5, 5, 3, 1, 1, 4]

        num_skills = len(self.skill_names)

        self.skill_mod_labels = []
        self.skill_mods = [0]*num_skills
        # All check boxes start false and flip when toggled
        self.skill_prof = [False]*num_skills
        self.expertise_prof = [False]*num_skills
        self.skill_checkbox = []
        self.expertise_checkbox = []

        for i, name in enumerate(self.skill_names):
            # Create button for rolling
            short_att = self.attribute_short[self.skill_type[i]]
            btn = QPushButton('{} ({})'.format(name, short_att), self)

            # create label showing modifier for this skill
            label = QLabel('+0', self)
            label.setMaximumWidth(30)
            self.skill_mod_labels.append(label)

            # create checkbox button for this skill
            checkbox = QCheckBox(self)
            self.skill_checkbox.append(checkbox)

            # create checkbox button for expertise in this skill
            expertise = QCheckBox(self)
            self.expertise_checkbox.append(expertise)

            self.skills_layout.addWidget(expertise, i, 0)
            self.skills_layout.addWidget(checkbox, i, 1)
            self.skills_layout.addWidget(label, i, 2)
            self.skills_layout.addWidget(btn, i, 3)

            # Connect checkbox button to proficiency
            checkbox.stateChanged.connect(partial(self.set_skill_prof, i))

            # Connect expertise button to expertise proficiency
            expertise.stateChanged.connect(partial(self.set_expertise_prof, i))

            # Connect the skill roll button to the skill roll function
            btn.clicked.connect(partial(self.skill_roll, i))

        # ---------------------------------------------------------------------
        # Passive Perception Section
        # ---------------------------------------------------------------------
        # Passive perception is just calculated and thus only uses labels
        self.passive_perception = QLabel('10', self)
        passive_perception_label = QLabel('Passive Perception', self)

        # Adding frames and stuff
        self.passive_perception.setFrameStyle(QtWidgets.QFrame.Panel)
        self.passive_perception.setLineWidth(2)
        self.passive_perception.setMaximumWidth(30)

        # Add and resize passive perception widgets
        self.pass_percep_layout.addWidget(passive_perception_label, 0, 1, 1, 3)
        self.pass_percep_layout.addWidget(self.passive_perception, 0, 0)

        # ---------------------------------------------------------------------
        # Attacks & Spellcasting Section
        # ---------------------------------------------------------------------
        self.attack_widget_list = []
        self.attack_list = []
        attacks_label = QLabel('Attacks & Spellcasting', self)
        attacks_label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                    QtWidgets.QSizePolicy.Fixed)

        section_labels = [QLabel('Name', self),
                          QLabel('Atk Bonus', self),
                          QLabel('Damage', self),
                          QLabel('Type', self)]
        self.add_attack_btn = QPushButton('+', self)
        self.attacks_layout.addWidget(self.add_attack_btn, 1, 5)

        # Add and resize attack widgets
        self.add_attack_btn.setMaximumWidth(30)
        self.attacks_layout.addWidget(attacks_label, 0, 1)

        for i in range(4):
            self.attacks_layout.addWidget(section_labels[i], 1, i)

        self.add_attack_btn.clicked.connect(self.add_attack)
        self.num_attacks = 0

        # Add invisible labels to keep from needing to resize existing widgets
        spacer = QLabel(' ', self)
        for i in range(2, 11):
            self.attacks_layout.addWidget(spacer, i, 0)

        # ---------------------------------------------------------------------
        # Roll log Section
        # ---------------------------------------------------------------------
        self.roll_log = QPlainTextEdit(self)
        self.roll_log.setReadOnly(True)
        self.roll_input = QLineEdit(self)

        self.log_layout.addWidget(self.roll_log, 0, 0, 10, 4)
        self.log_layout.addWidget(self.roll_input, 9, 0, 1, 4)

        self.roll_input.returnPressed.connect(self.manual_input)

        self.show()

    def write(self, text):
        """
        Handles writing output to the QPlainTextEdit widget
        """
        self.roll_log.appendPlainText(text)

    # Interpret dice rolls and modifiers entered as text
    def is_correctly_defined(self, roll):
        """
        Checks that each element of the string roll separated by a plus or
        minus is interpretable as a dice roll, a number, or a predefined
        modifier.
        """
        result = self.evaluate(roll)
        if result[0] is None:
            return False
        return True

    def evaluate(self, roll):
        """
        Does any dice rolling and modifier adding specified by the string roll
        """
        # parts will be a list of the dice rolls and modifiers along with the
        # plus and minus signs between them.
        if len(roll) == 0:
            return 0, 0

        last_sign = 1
        dice_val = 0
        mod = 0
        parts = re.split('(\+|-)', roll)

        short_att_list = [x.lower() for x in self.attribute_short]
        for p in parts:
            """
            Possibilities:
            1) p could be a plus or minus sign
            2) p could be a number, e.g. 2
            3) p could be a modifier, e.g. str, dex, int, prof, ect.
            4) p could be a dice roll, e.g. 1d20, 5d6, d8, ect.
            """

            if p == '+':
                last_sign = 1
            elif p == '-':
                last_sign = -1
            elif p.isdigit():
                mod += last_sign*int(p)
            elif p.lower() == 'prof':
                mod += last_sign*self.proficiency
            elif p.lower() in short_att_list:
                ind = short_att_list.index(p.lower())
                mod += last_sign*self.attribute_mods[ind]
            else:
                dice = p.split('d')
                if len(dice) > 0 and len(dice[0]) == 0:  # 'd10' is well defined
                    dice[0] = '1'
                if len(dice) != 2 or (not dice[0].isdigit()) or (not dice[1].isdigit()):
                    return None, None

                dice = [int(x) for x in dice]
                for i in range(dice[0]):
                    dice_val += last_sign*d(dice[1])

        return dice_val, mod

    # Rolls and other button connected things
    def write_roll(self, name, mod):
        r1 = d(20)
        r2 = d(20)

        self.write('{} roll'.format(name))
        self.write('{}+{} : {}+{}'.format(r1, mod, r2, mod))
        self.write('{} : {}'.format(r1+mod, r2+mod))
        self.write('')

    def attribute_roll(self, i):
        name = self.attribute_names[i]
        mod = self.attribute_mods[i]

        self.write_roll(name, mod)

    def saving_roll(self, i):
        name = self.attribute_names[i]+' Saving'
        mod = self.save_mods[i]

        self.write_roll(name, mod)

    def skill_roll(self, i):
        short_att = self.attribute_short[self.skill_type[i]]
        name = '{} ({})'.format(self.skill_names[i], short_att)
        mod = self.skill_mods[i]

        self.write_roll(name, mod)

    def add_attack(self):
        """
        In this function the button which adds more attacks is moved down,
        a text box is added for the name, attack bonus, damage, and type.
        Two buttons are added next to this, one rolls for attacks and the
        other rolls for damage.
        """

        self.num_attacks += 1
        # Force 9 attacks maximum so it looks good
        if self.num_attacks == 9:
            self.add_attack_btn.setVisible(False)

        curr_attack_ind = len(self.attack_widget_list)

        row = []
        for i in range(4):
            section = QLineEdit(self)
            self.attacks_layout.addWidget(section, self.num_attacks+1, i)
            section.setVisible(True)

            # Connect every section to the function that saves the info
            section.editingFinished.connect(partial(self.save_attack,
                                                    curr_attack_ind))

            row.append(section)

        # Add buttons
        attack_btn = QPushButton('Attack', self)
        attack_btn.setMaximumWidth(80)
        remove_btn = QPushButton('-', self)
        remove_btn.setMaximumWidth(30)

        self.attacks_layout.addWidget(attack_btn, self.num_attacks+1, 4)
        attack_btn.setVisible(True)

        self.attacks_layout.addWidget(remove_btn, self.num_attacks+1, 5)
        remove_btn.setVisible(True)

        attack_btn.clicked.connect(partial(self.attack_roll, curr_attack_ind))
        remove_btn.clicked.connect(partial(self.remove_attack,
                                           curr_attack_ind))

        row.append(attack_btn)
        row.append(remove_btn)

        self.attack_widget_list.append(row)
        # List to be filled when the row is used
        self.attack_list.append(['', '', '', ''])

    def remove_attack(self, i):
        """
        Remove this attack from the lists, move all attacks below it up by
        40 units as well as the add attack button.
        """
        self.num_attacks -= 1
        self.add_attack_btn.setVisible(True)

        for w in self.attack_widget_list[i]:
            w.deleteLater()

        self.attack_widget_list = (self.attack_widget_list[:i] +
                                   self.attack_widget_list[i+1:])
        self.attack_list = self.attack_list[:i]+self.attack_list[i+1:]

        for j in range(i, len(self.attack_widget_list)):
            for col, w in enumerate(self.attack_widget_list[j]):
                self.attacks_layout.removeWidget(w)
                self.attacks_layout.addWidget(w, j+2, col)

            attack_btn = self.attack_widget_list[j][-2]
            remove_btn = self.attack_widget_list[j][-1]
            attack_btn.clicked.disconnect()
            remove_btn.clicked.disconnect()
            attack_btn.clicked.connect(partial(self.attack_roll, j))
            remove_btn.clicked.connect(partial(self.remove_attack, j))

    def attack_roll(self, attack_ind):
        """
        Makes an attack roll. Rolls dice twice for advantage/disadvantage.
        Also rolls damage and adds on extra dice rolls if either d20 came up
        as a natural 20 e.g. (7+4) where the first number is the non-crit
        damage and the total is crit damage.
        """

        attack = self.attack_list[attack_ind]

        if len(attack[1]) > 0:
            # There usually isn't dice with an attack bonus, but I will add it
            # anyway. Can't hurt anything.
            dice, mod = self.evaluate(attack[1])
            atk_bonus = dice+mod

            r1 = d(20)
            r2 = d(20)

            self.write('{} attack roll'.format(attack[0]))
            self.write('{}+{} : {}+{}'.format(r1, atk_bonus, r2, atk_bonus))
            self.write('{} : {}'.format(r1+atk_bonus, r2+atk_bonus))
            self.write('')

            crit = (r1 == 20) or (r2 == 20)
        else:
            crit = False

        damage_dice, damage_mod = self.evaluate(attack[2])
        damage_value = damage_dice+damage_mod

        self.write('{} damage roll'.format(attack[0]))
        if crit:
            damage_dice2, _ = self.evaluate(attack[2])
            self.write('Critical damage: {}+{}'.format(damage_value,
                                                       damage_dice2))
        else:
            self.write('Damage: {}'.format(damage_value))
        self.write('')

    def manual_input(self):
        roll = self.roll_input.text()
        dice, mod = self.evaluate(roll)
        if dice is not None:
            self.write('{} = {}'.format(roll, dice+mod))
        else:
            self.write('Incorrect format.')
        self.roll_input.setText('')
        self.write('')

    # Functions to set or save values
    def set_modifier(self, i):
        textbox_value = self.attribute_score_input[i].text()

        if textbox_value.isdigit():
            score = int(textbox_value)
            self.attribute_scores[i] = score

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

    def set_skill_prof(self, i):
        self.skill_prof[i] = not self.skill_prof[i]
        if not self.skill_prof[i]:
            self.expertise_checkbox[i].setChecked(False)
        self.recalculate()

    def set_expertise_prof(self, i):
        self.expertise_prof[i] = not self.expertise_prof[i]
        if self.expertise_prof[i]:
            self.skill_checkbox[i].setChecked(True)
        self.recalculate()

    def save_attack(self, i):
        """
        This function should save data from the entire row of data.
        A list has already been added to self.attack_list in order to keep
        the place saved.
        Name can be anything
        attack bonus needs to be interpretable as a modifier (dice roll is ok)
        damage roll needs to be interpretable as a dice roll e.g. 3d10+5+str
        type can be anything
        """

        attack_textboxes = self.attack_widget_list[i][:4]
        data = [x.text() for x in attack_textboxes]
        if not self.is_correctly_defined(data[1]):
            data[1] = self.attack_list[i][1]
        if not self.is_correctly_defined(data[2]):
            data[2] = self.attack_list[i][2]
        self.attack_list[i] = data

    # Fixing all numbers and values section

    def recalculate(self):
        """
        Recalculates modifiers for saves and skills
        """
        # Saves
        for i in range(6):
            score = self.attribute_scores[i]
            mod = int(score//2)-5
            self.attribute_mods[i] = mod

            if self.save_prof[i]:
                mod += self.proficiency
            self.save_mods[i] = mod

        # Skills
        for i in range(len(self.skill_names)):
            att_ind = self.skill_type[i]
            mod = self.attribute_mods[att_ind]
            if self.skill_prof[i]:
                mod += self.proficiency
                if self.expertise_prof[i]:
                    mod += self.proficiency
            self.skill_mods[i] = mod

        passive_wis = str(10+self.skill_mods[11])
        self.passive_perception.setText(passive_wis)

        self.fix_labels()

    def fix_labels(self):
        """
        recalculate has fixed all the internal variables that may have been
        changed, this function will now fix the labels showing the modifiers
        to reflect this change.
        """

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

        for i in range(len(self.skill_names)):
            # skills
            mod = self.skill_mods[i]
            if mod >= 0:
                s = '+'+str(mod)
            else:
                s = str(mod)
            self.skill_mod_labels[i].setText(s)

    def fix_textboxes_and_checkboxes(self, new_save_prof, new_skill_prof):
        """
        This should only need to be called when a character is loaded in.
        Resets text boxes using the saved data so that they correctly
        reflect the internal state.
        """
        self.prof_textbox.setText(str(self.proficiency))

        for i in range(6):
            # attribute scores
            score = self.attribute_scores[i]
            self.attribute_score_input[i].setText(str(score))

            # save prof
            if self.save_prof[i] != new_save_prof[i]:
                checkbox = self.save_checkbox[i]
                checkbox.setChecked(new_save_prof[i])

        for i in range(len(self.skill_names)):
            # skill prof
            prof = self.skill_prof[i]
            checkbox = self.skill_checkbox[i]
            checkbox.setChecked(prof)
            if self.skill_prof[i] != new_skill_prof[i]:
                checkbox = self.skill_checkbox[i]
                checkbox.setChecked(new_skill_prof[i])


def main():
    app = QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())


main()
