# from dnd_roller import Character

import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication

import re
from functools import partial
from random import randint


def d(sides):
    value = randint(1, sides)
    return value


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        # startx, starty, width, height
        self.setGeometry(50, 50, 1200, 950)
        self.setWindowTitle('Unnamed Character')
        #self.setWindowIcon(QtGui.QIcon(''))  # set icon

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

        #self.setup()
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

        Variables relevant outside this function (anything besides static labels):
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
        left_margin = 10
        top_margin = 75
        small_spacing = 35
        large_spacing = 100

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
            label.move(left_margin+50-26//2, i*large_spacing+top_margin+30)

            textbox.resize(26, 20)
            textbox.move(left_margin+50-26//2, i*large_spacing+top_margin+50)

            btn.resize(100, 30)
            btn.move(left_margin, i*large_spacing+top_margin)

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
        prof_label.move(180, top_margin-30)

        self.prof_textbox.resize(26, 20)
        self.prof_textbox.move(150, top_margin-30)

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
            btn = QtWidgets.QPushButton(name, self)

            # create label showing modifier for this save
            label = QtWidgets.QLabel('+0', self)
            self.save_mod_labels.append(label)

            # create checkbox button for this save
            checkbox = QtWidgets.QCheckBox(self)
            self.save_checkbox.append(checkbox)

            # Move and resize everything
            label.resize(26, 30)
            label.move(175, i*small_spacing+top_margin)

            checkbox.resize(26, 30)
            checkbox.move(155, i*small_spacing+top_margin)

            btn.resize(100, 30)
            btn.move(200, i*small_spacing+top_margin)

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
        self.skill_prof = [False]*num_skills  # all buttons start off, flip when toggled
        self.skill_checkbox = []

        for i, name in enumerate(self.skill_names):
            # Create button for rolling
            short_att = self.attribute_short[self.skill_type[i]]
            btn = QtWidgets.QPushButton('{} ({})'.format(name, short_att), self)

            # create label showing modifier for this save
            label = QtWidgets.QLabel('+0', self)
            self.skill_mod_labels.append(label)

            # create checkbox button for this save
            checkbox = QtWidgets.QCheckBox(self)
            self.skill_checkbox.append(checkbox)

            # Move and resize everything
            label.resize(26, 30)
            label.move(175, i*small_spacing+300)

            checkbox.resize(26, 30)
            checkbox.move(155, i*small_spacing+300)

            btn.resize(200, 30)
            btn.move(200, i*small_spacing+300)

            # Connect checkbox button to proficiency
            checkbox.stateChanged.connect(partial(self.set_skill_prof, i))

            # Connect the skill roll button to the skill roll function
            btn.clicked.connect(partial(self.skill_roll, i))

        # ---------------------------------------------------------------------
        # Passive Perception Section
        # ---------------------------------------------------------------------
        # Passive perception is just calculated and thus only uses labels
        self.proficiency = 2
        self.passive_perception = QtWidgets.QLabel('10', self)
        passive_perception_label = QtWidgets.QLabel('Passive\nPerception', self)

        # Move and resize proficiency things
        passive_perception_label.resize(75, 40)
        passive_perception_label.move(40, 700)

        self.passive_perception.resize(26, 20)
        self.passive_perception.move(left_margin, 707)

        # ---------------------------------------------------------------------
        # Attacks & Spellcasting Section
        # ---------------------------------------------------------------------
        self.attack_widget_list = []
        self.attack_list = []
        attacks_label = QtWidgets.QLabel('Attacks & Spellcasting', self)

        section_labels = [QtWidgets.QLabel('Name', self),
                          QtWidgets.QLabel('Atk Bonus', self),
                          QtWidgets.QLabel('Damage', self),
                          QtWidgets.QLabel('Type', self)]
        self.add_attack_btn = QtWidgets.QPushButton('+', self)

        # Move and resize attack things
        attacks_label.resize(160, 20)
        attacks_label.move(550, top_margin-20)

        self.section_labels_pos = [450, 590, 730, 880]
        for i in range(4):
            section_labels[i].resize(len(section_labels[i].text())*11, 20)
            section_labels[i].move(self.section_labels_pos[i], top_margin+10)

        self.add_attack_btn.resize(20, 20)
        self.add_attack_btn.move(550, top_margin+40)

        self.add_attack_btn.clicked.connect(self.add_attack)

        # ---------------------------------------------------------------------
        # Roll log Section
        # ---------------------------------------------------------------------
        self.roll_log = QtWidgets.QPlainTextEdit(self)
        self.roll_log.setReadOnly(True)
        self.roll_input = QtWidgets.QLineEdit(self)

        self.roll_log.resize(700, 380)
        self.roll_log.move(self.section_labels_pos[0], 500)

        self.roll_input.resize(700, 20)
        self.roll_input.move(self.section_labels_pos[0], 500+380)

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

        xpos = self.add_attack_btn.x()
        ypos = self.add_attack_btn.y()

        # move button down
        self.add_attack_btn.move(xpos, ypos+40)

        # Add all the text boxes
        section_textbox_sizes = [125, 125, 125, 100]

        curr_attack_ind = len(self.attack_widget_list)

        row = []
        for i in range(4):
            section = QtWidgets.QLineEdit(self)
            section.resize(section_textbox_sizes[i], 20)
            section.move(self.section_labels_pos[i], ypos)
            section.setVisible(True)

            # Connect every section to the function that saves the info
            section.editingFinished.connect(partial(self.save_attack, curr_attack_ind))

            row.append(section)

        # Add buttons
        attack_btn = QtWidgets.QPushButton('Attack', self)
        remove_btn = QtWidgets.QPushButton('-', self)

        attack_btn.resize(55, 30)
        attack_btn.move(1010, ypos-5)
        attack_btn.setVisible(True)

        remove_btn.resize(30, 30)
        remove_btn.move(1085, ypos-5)
        remove_btn.setVisible(True)

        attack_btn.clicked.connect(partial(self.attack_roll, curr_attack_ind))
        remove_btn.clicked.connect(partial(self.remove_attack, curr_attack_ind))

        row.append(attack_btn)
        row.append(remove_btn)

        self.attack_widget_list.append(row)
        self.attack_list.append(['', '', '', ''])  # List to be filled when the row is used

    def remove_attack(self, i):
        """
        Remove this attack from the lists, move all attacks below it up by
        40 units as well as the add attack button.
        """
        for w in self.attack_widget_list[i]:
            w.deleteLater()

        self.attack_widget_list = self.attack_widget_list[:i]+self.attack_widget_list[i+1:]
        self.attack_list = self.attack_list[:i]+self.attack_list[i+1:]

        for j in range(i, len(self.attack_widget_list)):
            for w in self.attack_widget_list[j]:
                w.move(w.x(), w.y()-40)

            attack_btn = self.attack_widget_list[j][-2]
            remove_btn = self.attack_widget_list[j][-1]
            attack_btn.clicked.disconnect()
            remove_btn.clicked.disconnect()
            attack_btn.clicked.connect(partial(self.attack_roll, j))
            remove_btn.clicked.connect(partial(self.remove_attack, j))

        xpos = self.add_attack_btn.x()
        ypos = self.add_attack_btn.y()
        self.add_attack_btn.move(xpos, ypos-40)

    def attack_roll(self, attack_ind):
        """
        Makes an attack roll. Rolls dice twice for advantage/disadvantage.
        Also rolls damage and adds on extra dice rolls if either d20 came up
        as a natural 20 e.g. (7+4) where the first number is the non-crit
        damage and the total is crit damage.
        """

        attack = self.attack_list[attack_ind]

        # There usually isn't dice with an attack bonus, but I will add it in
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
        damage_dice, damage_mod = self.evaluate(attack[2])
        damage_value = damage_dice+damage_mod

        self.write('{} damage roll'.format(attack[0]))
        if crit:
            damage_dice2, _ = self.evaluate(attack[2])
            self.write('Critical damage: {}+{}'.format(damage_value, damage_dice2))
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
        self.recalculate()

    def save_attack(self, i):
        """
        This function should save data from the entire row of data.
        A list has already been added to self.attack_list in order to keep
        the place saved.
        Name can be anything
        attack bonus needs to be interpretable as a modifier (technically could include dice roll how I have checked it)
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
