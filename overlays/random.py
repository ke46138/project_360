import random

from modules import admin_arbuz

original_randint = random.randint
original_random = random.random

def randint_overlay(a: int, b: int) -> int:
    if admin_arbuz.FORCE_RANDOM_VALUE:
        value = admin_arbuz.FORCE_RANDOM_VALUE
        admin_arbuz.FORCE_RANDOM_VALUE = False

        return value
    else:
        return original_randint(a, b)

def random_overlay() -> float:
    if admin_arbuz.FORCE_RANDOM_VALUE:
        value = admin_arbuz.FORCE_RANDOM_VALUE
        admin_arbuz.FORCE_RANDOM_VALUE = False

        if value > 1:
            return 1
        else:
            return value
    else:
        return original_random()

random.randint = randint_overlay
random.random = random_overlay
