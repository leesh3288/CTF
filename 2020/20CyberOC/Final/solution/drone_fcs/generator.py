# coding: utf-8

from __future__ import print_function

import warnings
import random
import copy
import time
import sys

# For console mode
from hash_functions import djb2_32, djb2_64


class GreedyGenerator:
    TOTAL_LETTERS = 32
    TOTAL_ROUNDS = 10
    MUTATION_MOD = 2
    BYTES_TO_MUTATE = TOTAL_LETTERS // MUTATION_MOD
    ALPHABET = '__all__'
    VERBOSE = False

    def __init__(self, hash_function, target_value, total_letters=TOTAL_LETTERS):
        self.TOTAL_LETTERS = total_letters
        if self.TOTAL_LETTERS <= 0:
            raise Exception("Impossibru!")
        self.string_to_guess = bytearray(b"\0" * self.TOTAL_LETTERS)
        self.checker = hash_function
        self.target = target_value

    def set_target(self, new_target):
        self.target = new_target

    def set_collision_size(self, new_size):
        self.TOTAL_LETTERS = new_size
        self.string_to_guess = bytearray(b"\0" * self.TOTAL_LETTERS)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def _paste_to_c(self, general):
        total_letters = len(general)
        paster = "char kek[%d] = {" % (total_letters + 1)
        # little endian
        numbs = ", ".join([str(bt) for bt in general])
        paster += numbs + ", 0x00 };"
        return paster

    def _get_all_possible_values(self, letter_index):
        all_possible_values = {}
        for i in range(256):
            self.string_to_guess[letter_index] = i
            hash_value = self.checker(self.string_to_guess)
            all_possible_values[i] = hash_value
        return all_possible_values

    def _check_if_got_it(self, letter_index, all_possible_values, target):
        for byte, hash_value in all_possible_values.items():
            got_it = (hash_value == target)
            if got_it:
                self.string_to_guess[letter_index] = byte
                HASH_GENERAL = copy.copy(self.string_to_guess)
                return True, HASH_GENERAL
        return False, self.string_to_guess

    def next(self):
        self.string_to_guess = self.mutate_full(self.string_to_guess)
        got_it = False
        while not got_it:
            prev_round_value = None
            for round_numb in range(self.TOTAL_ROUNDS):
                for letter_index in range(self.TOTAL_LETTERS):
                    all_possible_values = self._get_all_possible_values(letter_index)
                    got_it, winner = self._check_if_got_it(letter_index, all_possible_values, self.target)
                    if got_it:
                        return winner
                    sorted_hashes = [k for k in all_possible_values.keys()]
                    # Ключевая строка:
                    # Жадно отбираем победившую букву. Победила та, что ближе всех перенесла нас к цели
                    sorted_hashes.sort(key=lambda asc_letter: abs(self.target - all_possible_values[asc_letter]))
                    self.string_to_guess[letter_index] = sorted_hashes[0]
                current_best = all_possible_values[sorted_hashes[0]]
                if self.VERBOSE:
                    print("%d ROUND:" % round_numb, current_best, abs(self.target - current_best))
                if self.string_to_guess == prev_round_value:
                    # useless round, mutate and try next
                    # or return winner and mutate
                    break
                prev_round_value = copy.copy(self.string_to_guess)
            self.string_to_guess = self.mutate_partial(self.string_to_guess)

    def mutate_partial(self, target):
        for _ in range(self.BYTES_TO_MUTATE):
            position = random.randint(0, self.TOTAL_LETTERS - 1)
            new_value = random.randint(0, 255)
            target[position] = new_value
        return target

    def mutate_full(self, target):
        return bytearray(random.sample(range(256), self.TOTAL_LETTERS))


if __name__ == "__main__":
    # Output to stdout
    target = sys.argv[1]
    try:
        target = int(target)
    except ValueError:
        print("Nope. Can not represent as 10 base int", file=sys.stderr)
        exit(1)
    try:
        string_size = sys.argv[2]
        string_size = int(string_size)
    except IndexError:
        string_size = GreedyGenerator.TOTAL_LETTERS
    except ValueError:
        warnings.warn("Nope. Can not parse string size")
        string_size = GreedyGenerator.TOTAL_LETTERS

    func = lambda x: x
    if target < 0 or target >= 2 ** 64:
        print("Nope. Wrong size. >= 0, but < 2^64", file=sys.stderr)
        exit(1)
    if target < 2**32:
        func = djb2_32
    elif target >= 2 ** 32 and target < 2**64:
        func = djb2_64

    start = time.clock()
    gen = GreedyGenerator(func, target, string_size)
    total_generated = set()
    consecutive_misses = 0
    try:
        while consecutive_misses < 100:
            for next_collision in gen:
                bnext_collision = bytes(next_collision)
                if bnext_collision not in total_generated:
                    print(bnext_collision)
                    total_generated.add(bnext_collision)
                    consecutive_misses = 0
                else:
                    consecutive_misses += 1
                if consecutive_misses >= 100:
                    break
            print("Can not find more collisions with %d length. Switching to +1 length" % gen.TOTAL_LETTERS)
            consecutive_misses = 0
            gen.set_collision_size(gen.TOTAL_LETTERS + 1)
    except KeyboardInterrupt:
        end = time.clock()
        time_seconds = end - start
        print("Generation interrupted. Total generated %d collisions for %d target" % (len(total_generated), target))
        print("Time spent: %d seconds. Average speed is %.4f collisions/sec" %
              (time_seconds, len(total_generated) / time_seconds))
