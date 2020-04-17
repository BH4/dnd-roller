from random import randint


def d(sides, verbose=False):
    value = randint(1, sides)
    if verbose:
        print('Rolled a d'+str(sides)+' and got a '+str(value)+'!')
    return value


def roll_with(advantage=False, disadvantage=False, verbose=False):
    if advantage and disadvantage:
        advantage = False
        disadvantage = False

    if advantage:
        result = max(d(20, verbose=verbose), d(20, verbose=verbose))
    elif disadvantage:
        result = min(d(20, verbose=verbose), d(20, verbose=verbose))
    else:
        result = d(20, verbose=verbose)
    return result


class Character:
    def __init__(self):
        # variables: prof, str, dex, con, int, wis, chr
        self.score_full_names = ['proficiency', 'strength', 'dexterity',
                                 'constitution', 'intelligence', 'wisdom',
                                 'charisma']
        self.score_names = ['prof', 'str', 'dex', 'con', 'int', 'wis', 'chr']

        self.shorthand = dict()
        for i in range(len(self.score_full_names)):
            self.shorthand[self.score_full_names[i]] = self.score_names[i]

        # For the purposes here skills include saving throws.
        str_base = ['strength', 'save(strength)', 'athletics']
        dex_base = ['dexterity', 'save(dexterity)', 'acrobatics', 'sleight of hand', 'stealth']
        con_base = ['constitution', 'save(constitution)']
        int_base = ['intelligence', 'save(intelligence)' 'arcana', 'history', 'investigation', 'nature', 'religion']
        wis_base = ['wisdom', 'save(wisdom)', 'animal', 'handling', 'insight', 'medicine', 'perception', 'survival']
        chr_base = ['charisma', 'save(charisma)', 'deception', 'intimidation', 'performance', 'persuasion']
        # Note this is in the same order as score_names
        temp_skills = [str_base, dex_base, con_base, int_base, wis_base, chr_base]

        # Each skill will be a key whose value is its base stat.
        self.skills = dict()
        for i in range(1, len(self.score_names)):
            s_list = temp_skills[i-1]

            for s in s_list:
                self.skills[s] = self.score_names[i]

        self.scores = dict()  # [2, 10, 10, 10, 10, 10, 10]
        # Any name in here means it has proficiency.
        self.proficiencies = set()

        # read ability scores and list of proficiencies.
        self.get_stats()

        self.mods = dict()
        self.set_modifiers()

        # read predefined rolls
        self.defined_rolls = dict()
        self.get_predefined_rolls()

    def fix_save_names(self, name):
        if name != 'proficiency' and name in self.score_full_names:
            # This is actually a save
            return 'save('+name+')'
        return name

    def set_ability_score(self, line):
        # Note that this also works for the proficiency line.

        # Correct input should have an ability score name and a number
        # (as a string) after the next line.
        sides = [x.strip().lower() for x in line.split('=')]

        if len(sides) != 2 or sides[0] not in self.score_full_names:
            raise SyntaxError('Incorrectly formated ability score.')

        try:
            sides[1] = int(sides[1])
        except ValueError as err:
            raise ValueError('Incorrectly formated ability score. Score must be integer.')

        # ability_index = self.score_full_names.index(sides[0])
        # self.scores[ability_index] = sides[1]
        self.scores[sides[0]] = sides[1]

    def set_proficiency(self, line):
        prof = line.strip().lower()

        prof = self.fix_save_names(prof)

        if prof not in self.skills:
            raise SyntaxError(prof+' not within list of skills or saves.')

        self.proficiencies.add(prof)

    def get_stats(self):
        filename = 'ability_scores_and_proficiencies.txt'

        with open(filename, 'r') as f:
            for line in f:
                # Lines that aren't empty and aren't comments should be ability
                # scores or proficiencies.
                if len(line.strip()) > 0 and line[0] != '#':
                    if '=' in line:
                        self.set_ability_score(line)
                    else:
                        self.set_proficiency(line)

    def set_modifiers(self):
        for s in self.scores:
            val = self.scores[s]

            short = self.shorthand[s]
            if s == 'proficiency':
                self.mods[short] = val
            else:
                self.mods[short] = int(val//2)-5

    def get_predefined_rolls(self):
        filename = 'common_rolls.txt'

        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Lines that aren't empty and aren't comments should be
                # roll definitions.
                if len(line) > 0 and line[0] != '#':
                    definition = line.split(':')
                    if ':' not in line or len(definition) != 3:
                        print(':' not in line, definition)
                        raise SyntaxError('"'+line+'" not correctly defined roll.')

                    name = definition[0].strip().lower()
                    attack_roll = definition[1].strip().lower()
                    damage_roll = definition[2].strip().lower()

                    self.defined_rolls[name] = (attack_roll, damage_roll)

    # Begin defining rolls
    def interp_roll(self, desc, verbose=False):
        """
        Given a roll description, such as 1d20+str+prof, return the correct
        values added to the correct roll. The example would be a single d20
        roll added to strength modifier and the proficiency bonus.
        """
        parts = desc.split('+')
        tot = 0
        for p in parts:
            """
            Possibilities:
            1) p could be a dice roll, e.g. 1d20, 5d6, d8, ect.
            2) p could be a modifier, e.g. str, dex, int, prof, ect.
            3) p could be a number (sword of +2)
            """
            if p in self.mods:  # 2
                if verbose:
                    print('Adding '+p)
                tot += self.mods[p]
            elif 'd' in p:  # 1
                num, die = p.split('d')
                if len(num) == 0:
                    num = 1
                else:
                    num = int(num)
                die = int(die)

                for i in range(num):
                    tot += d(die, verbose=verbose)
            else:  # 3
                if verbose:
                    print('+'+p)
                tot += int(p)
        return tot

    def roll(self, name, advantage=False, disadvantage=False, verbose=False):
        # Possibilities:
        # 1) name is the name of a predefined roll
        # 2) name is a skill within self.skills (saving throws too)
        name = name.strip()
        name = name.lower()

        if name in self.defined_rolls:
            attack, damage = self.defined_rolls[name]
            if verbose:
                print('Making attack roll.')
            ar = self.interp_roll(attack, verbose=verbose)
            if verbose:
                print('Making damage roll.')
            dr = self.interp_roll(damage, verbose=verbose)
            return (ar, dr)

        # If 'save' is somewhere in name and it wasn't a predefined roll
        # then I should fix it so that it says save(skill)
        if 'save' in name:
            for s in self.score_full_names:
                if s in name:
                    name = self.fix_save_names(s)
                    break

        if name in self.skills:
            score_name = self.skills[name]

            result = roll_with(advantage=advantage, disadvantage=disadvantage, verbose=verbose)

            result += self.mods[score_name]
            description = 'Added '+score_name+' modifier'

            if name in self.proficiencies:
                result += self.mods['prof']
                description += ' with proficiency'
            description += '!'
            if verbose:
                print(description)
            return result

        raise ValueError('"'+name+'" roll name not defined.')


if __name__ == '__main__':
    c = Character()
    print(c.defined_rolls)

    curr = input('Roll name: ').strip().lower()
    while curr != 'done':
        if 'with' in curr:
            curr, adv = [x.strip() for x in curr.split('with')]
            if adv == 'adv' or adv == 'advantage':
                advantage = True
                disadvantage = False
            elif adv == 'disadvantage' or adv == 'dis':
                advantage = False
                disadvantage = True
            else:
                raise SyntaxError('Advantage name not defined.')

            print(c.roll(curr, advantage=advantage, disadvantage=disadvantage, verbose=True))
        else:
            print(c.roll(curr, verbose=True))

        curr = input('Roll name: ').strip().lower()

"""
ToDo:
Create GUI

Make sure attack rolls can have advantage.
"""
