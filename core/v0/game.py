from v0.tools import (
    calculate_bulls_cows,
    guess_based_on_score,
    initialize,
    safe_log2,
    tuple_to_string,
)
import pandas as pd
import random
import numpy as np
from itertools import permutations


class BullsNCows:
    def __init__(self, digits=4, guess_algorithm=guess_based_on_score, verbose=False):
        permute = permutations([i for i in range(10)], digits)
        self.originals = [tuple_to_string(p) for p in list(permute)]
        self.org_idx_map = {org: idx for idx, org in enumerate(self.originals)}
        self.digits = digits
        self.guess = guess_algorithm
        self.verbose = verbose
        self.reset()

        initialize(originals=self.originals, digits=4)

    def reset(self):
        self.guesses = {}
        self.secret = random.choice(self.originals)
        self.summary = [
            {
                "guess": "",
                "guess_result": "",
                "candidate_count": len(self.originals),
                "candidate_entropy": safe_log2(len(self.originals)),
                "guess_actual_entropy": np.NaN,
                "best_guess_entropy": np.NaN,
                "best_guess": "",
            }
        ]

    def next(self):
        if len(self.guesses) > 0:
            guess = self.summary[-1]["best_guess"]
        else:
            guess = random.choice(self.originals)
            # idx = self.org_idx_map[guess]
            # bulls_n_cows_map = read_bulls_n_cows_map(digits=self.digits)

            self.summary[-1]["best_guess"] = guess
            # self.summary[-1]['best_guess_entropy'] = entropy([len(bulls_n_cows_map[idx][bc]) for bc in bulls_n_cows_map[idx]], base=2)

        guess_result = calculate_bulls_cows(self.secret, guess)
        candidate_count, best_guess, best_guess_entropy = self.guess(
            originals=self.originals,
            org_idx_map=self.org_idx_map,
            guesses=self.guesses,
            guess=guess,
            bulls_n_cows=guess_result,
            digits=self.digits,
            candidate_entropy=self.summary[-1]["candidate_entropy"],
            verbose=self.verbose,
        )

        self.summary.append(
            {
                "guess": guess,
                "guess_result": guess_result,
                "candidate_count": candidate_count,
                "candidate_entropy": safe_log2(candidate_count),
                "guess_actual_entropy": self.summary[-1]["candidate_entropy"]
                - safe_log2(candidate_count),
                "best_guess_entropy": best_guess_entropy,
                "best_guess": best_guess,
            }
        )

        return self

    def play(self, n_iter=10):
        self.reset()
        print(self.secret)
        while self.summary[-1]["guess"] != self.secret and n_iter > 0:
            self.next()
            n_iter -= 1

        return pd.DataFrame.from_dict(self.summary)
