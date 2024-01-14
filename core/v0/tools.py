import math
import random
import numpy as np
import pickle
import os.path
from scipy.stats import entropy


def safe_log2(x):
    return math.log2(x) if x > 0 else 0


def tuple_to_string(num_tuple):
    return "".join(map(str, num_tuple))


def calculate_bulls_cows(source, target):
    if len(source) != len(target):
        raise ValueError("Input arrays must have the same length")

    bulls = sum(s == t for s, t in zip(source, target))
    common_digits = set(source) & set(target)
    cows = (
        sum(min(source.count(digit), target.count(digit)) for digit in common_digits)
        - bulls
    )

    return bulls, cows


def parse_bulls_n_cows_map_name(digits, guesses={}):
    suffix = "".join(f"_{k}:{v[0]}{v[1]}" for (k, v) in sorted(guesses.items()))
    return f"bulls_n_cows_map/{digits}{suffix}.pkl"


def initialize(originals, digits):
    filepath = parse_bulls_n_cows_map_name(digits=digits)
    if os.path.isfile(filepath):
        return

    bulls_n_cows_map = {}
    for i, _ in enumerate(originals):
        bulls_n_cows_map[i] = {}
        for di in range(digits + 1):
            for dj in range(di + 1):
                bulls_n_cows_map[i][(dj, di - dj)] = set()

    for i, source in enumerate(originals):
        bulls_n_cows_map[i][(digits, 0)].add(i)
        for j in range(i):
            target = originals[j]
            bulls_n_cows = calculate_bulls_cows(source, target)
            bulls_n_cows_map[i][bulls_n_cows].add(j)
            bulls_n_cows_map[j][bulls_n_cows].add(i)

    with open(filepath, "wb") as f:
        pickle.dump(bulls_n_cows_map, f, protocol=pickle.HIGHEST_PROTOCOL)


def convert_bulls_n_cows_map(originals, bulls_n_cows_map):
    return {
        originals[i]: {
            bc: set(originals[j] for j in bulls_n_cows_map[i][bc])
            for bc in bulls_n_cows_map[i]
            if len(bulls_n_cows_map[i][bc]) > 0
        }
        for i in bulls_n_cows_map
    }


def read_bulls_n_cows_map(digits, curr_guesses={}):
    filepath = parse_bulls_n_cows_map_name(digits, curr_guesses)
    if not os.path.isfile(filepath):
        return None

    with open(filepath, "rb") as f:
        bulls_n_cows_map = pickle.load(f)

    return bulls_n_cows_map


def update_bulls_n_cows_map(org_idx_map, guess, bulls_n_cows, digits, curr_guesses={}):
    next_guesses = curr_guesses.copy()
    next_guesses[guess] = bulls_n_cows

    filepath = parse_bulls_n_cows_map_name(digits=digits, guesses=next_guesses)
    if os.path.isfile(filepath):
        return read_bulls_n_cows_map(digits=digits, curr_guesses=next_guesses)

    bulls_n_cows_map = read_bulls_n_cows_map(digits=digits, curr_guesses=curr_guesses)

    guess_idx = org_idx_map[guess]
    candidates = bulls_n_cows_map[guess_idx][bulls_n_cows]

    for src_idx in bulls_n_cows_map:
        for bc in bulls_n_cows_map[src_idx]:
            bulls_n_cows_map[src_idx][bc] = bulls_n_cows_map[src_idx][bc].intersection(
                candidates
            )

    with open(filepath, "wb") as f:
        pickle.dump(bulls_n_cows_map, f, protocol=pickle.HIGHEST_PROTOCOL)

    return bulls_n_cows_map


def calc_candidates(bulls_n_cows_map):
    candidates = set()
    for src_idx in bulls_n_cows_map:
        for bc in bulls_n_cows_map[src_idx]:
            candidates = candidates.union(bulls_n_cows_map[src_idx][bc])

    return candidates


def calc_entropy_score_map(
    bulls_n_cows_map, candidates, candidate_entropy, guess_count, calc_entropy_score=np.sqrt
):
    entropy_map = {}
    score_map = {}

    C = len(candidates)
    for idx in bulls_n_cows_map:
        factor = (1 - 1 / C) if idx in candidates else 1
        entropy_map[idx] = entropy(
            [len(bulls_n_cows_map[idx][bc]) for bc in bulls_n_cows_map[idx]], base=2
        )
        score_map[idx] = (
            guess_count + calc_entropy_score(candidate_entropy - entropy_map[idx]) * factor
        )

    return entropy_map, score_map


def guess_based_on_candidates(
    originals,
    org_idx_map,
    digits,
    guesses,
    guess,
    bulls_n_cows,
    candidate_entropy,
    calc_entropy_score=np.sqrt,
    verbose=False,
):
    bulls_n_cows_map = update_bulls_n_cows_map(
        org_idx_map=org_idx_map,
        digits=digits,
        curr_guesses=guesses,
        guess=guess,
        bulls_n_cows=bulls_n_cows,
    )

    guesses[guess] = bulls_n_cows
    candidates = calc_candidates(bulls_n_cows_map=bulls_n_cows_map)

    if verbose:
        print("\n💬", guesses)
        print("🎯", sorted([originals[c] for c in candidates]))

    if len(candidates) == 0:
        return 0, None, None
    elif len(candidates) == 1:
        return 1, originals[list(candidates)[0]], None

    entropy_map, score_map = calc_entropy_score_map(
        bulls_n_cows_map=bulls_n_cows_map,
        candidates=candidates,
        candidate_entropy=candidate_entropy,
        guess_count=len(guesses),
        calc_entropy_score=calc_entropy_score,
    )
    best_guess = random.choice(list(candidates))

    if verbose:
        candidate_map = {}
        for idx in entropy_map:
            entropy = f"{entropy_map[idx]:.2f}B"
            if entropy in candidate_map:
                candidate_map[entropy].add(originals[idx])
            else:
                candidate_map[entropy] = set([originals[idx]])

        print(
            f"🎲 {safe_log2(len(candidates)):.2f}B - {entropy_map[best_guess]:.2f}B | {score_map[best_guess]:.2f}P ('{originals[best_guess]}')")
        print(sorted(candidate_map.items(), key=lambda item: item[0]))

    return len(candidates), originals[best_guess], entropy_map[best_guess]


def guess_based_on_entropy(
    originals,
    org_idx_map,
    digits,
    guesses,
    guess,
    bulls_n_cows,
    candidate_entropy,
    calc_entropy_score=np.sqrt,
    verbose=False,
):
    bulls_n_cows_map = update_bulls_n_cows_map(
        org_idx_map=org_idx_map,
        digits=digits,
        curr_guesses=guesses,
        guess=guess,
        bulls_n_cows=bulls_n_cows,
    )

    guesses[guess] = bulls_n_cows
    candidates = calc_candidates(bulls_n_cows_map=bulls_n_cows_map)

    if verbose:
        print("\n💬", guesses)
        print("🎯", sorted([originals[c] for c in candidates]))

    if len(candidates) == 0:
        return 0, None, None
    elif len(candidates) == 1:
        return 1, originals[list(candidates)[0]], None

    entropy_map, score_map = calc_entropy_score_map(
        bulls_n_cows_map=bulls_n_cows_map,
        candidates=candidates,
        candidate_entropy=candidate_entropy,
        guess_count=len(guesses),
        calc_entropy_score=calc_entropy_score,
    )
    best_guess = max(entropy_map, key=entropy_map.get)

    if verbose:
        candidate_map = {}
        for idx in entropy_map:
            entropy = f"{entropy_map[idx]:.2f}B"
            if entropy in candidate_map:
                candidate_map[entropy].add(originals[idx])
            else:
                candidate_map[entropy] = set([originals[idx]])

        print(
            f"🎲 {safe_log2(len(candidates)):.2f}B - {entropy_map[best_guess]:.2f}B | {score_map[best_guess]:.2f}P ('{originals[best_guess]}')")
        print(sorted(candidate_map.items(), key=lambda item: item[0]))

    return len(candidates), originals[best_guess], entropy_map[best_guess]


def guess_based_on_score(
    originals,
    org_idx_map,
    digits,
    guesses,
    guess,
    bulls_n_cows,
    candidate_entropy,
    calc_entropy_score=np.sqrt,
    verbose=False,
):
    bulls_n_cows_map = update_bulls_n_cows_map(
        org_idx_map=org_idx_map,
        digits=digits,
        curr_guesses=guesses,
        guess=guess,
        bulls_n_cows=bulls_n_cows,
    )

    guesses[guess] = bulls_n_cows
    candidates = calc_candidates(bulls_n_cows_map=bulls_n_cows_map)

    if verbose:
        print("\n💬", guesses)
        print("🎯", sorted([originals[c] for c in candidates]))

    if len(candidates) == 0:
        return 0, None, None
    elif len(candidates) == 1:
        return 1, originals[list(candidates)[0]], None

    entropy_map, score_map = calc_entropy_score_map(
        bulls_n_cows_map=bulls_n_cows_map,
        candidates=candidates,
        candidate_entropy=candidate_entropy,
        guess_count=len(guesses),
        calc_entropy_score=calc_entropy_score,
    )
    best_guess = min(score_map, key=score_map.get)

    if verbose:
        candidate_map = {}
        for idx in score_map:
            score = f"{score_map[idx]:.2f}P"
            if score in candidate_map:
                candidate_map[score].add(originals[idx])
            else:
                candidate_map[score] = set([originals[idx]])

        print(
            f"🎲 {safe_log2(len(candidates)):.2f}B - {entropy_map[best_guess]:.2f}B | {score_map[best_guess]:.2f}P ('{originals[best_guess]}')")
        print(sorted(candidate_map.items(), key=lambda item: item[0]))

    return len(candidates), originals[best_guess], entropy_map[best_guess]
