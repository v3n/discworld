import itertools
import json

from sympy import Symbol, Function, log, sqrt, floor, ceiling, exp
from sympy import Piecewise, log, piecewise_fold
from sympy import integrate
from sympy.solvers import solve


class StatMultiplier(Function):
    @classmethod
    def eval(cls, a, b, c, d, e):
        return (1 / 9.8) * log(a * b * c * d * e) - 0.25


class RawLevelBonus(Function):
    @classmethod
    def eval(cls, level):
        return Piecewise(
            (5 * level, level <= 20),
            (2.5 * level - 20 + 100, level <= 40),
            (level - 40 + 150, level <= 60),
            (0.5 * (level - 60) + 170, True),
        )


class Bonus(Function):
    @classmethod
    def eval(cls, level, a, b, c, d, e):
        return StatMultiplier(a, b, c, d, e) * RawLevelBonus(level)


class GPRegen(Function):
    @classmethod
    def eval(cls, a, b, c, d, e):
        return sqrt(175 * StatMultiplier(a, b, c, d, e)) - 10


class XPCostFromPlayer(Function):
    @classmethod
    def eval(cls, level):
        return (250 + 125) * level * exp(level / 500)


CON = 0
DEX = 1
INT = 2
STR = 3
WIS = 4


def ArrangeToSkill(skill, arrange):
    STAT_REMAP = {
        'S': STR,
        'C': CON,
        'D': DEX,
        'I': INT,
        'W': WIS,
    }

    params = []

    for c in skill:
        params.append(arrange[STAT_REMAP[c]])

    return params


SKILLS = {
    "fighting": {
        "melee": {
            "axe": "CDSSS",
            "dagger": "DDDDS",
            "flail": "CDDSS",
            "heavy-sword": "CDSSS",
            "mace": "CCDSS",
            "misc": "CDDSS",
            "polearm": "CCSSS",
            "sword": "DDDSS",
        },
        "defense": {
          "dodge": "DDDDW",
          "parry": "DDDSW",
        },
        "special": {
            "tactics": "WWIII",
            "weapon": "SDIII",
        },
    },
    "methods": {
        "air": "IICCC",
        "earth": "IICCC",
        "fire": "IICCC",
        "water": "IICCC",
        "animating": "IIIII",
        "channeling": "IIIII",
        "charming": "IIIII",
        "convoking": "IIIII",
        "cursing": "IIIII",
        "binding": "IIDDD",
        "brewing": "IIDDD",
        "chanting": "IIDDD",
        "dancing": "IIDDD",
        "enchanting": "IIDDD",
        "evoking": "IIDDD",
        "healing": "IIDDD",
        "scrying": "IIDDD",
        "abjuring": "IIWWW",
        "banishing": "IIWWW",
        "conjuring": "IIWWW",
        "divining": "IIWWW",
        "summoning": "IIWWW",

        "points": "IISWW",
    },
    "spells": {
        "defensive": "WCCII",
        "misc": "WDDII",
        "offensive": "WSSII",
        "special": "WWWII",
    }
}


def findBestMelee(arrange):
    meleeSkill = ""
    meleeLevel = 99999
    defenseSkill = ""
    defenseLevel = 99999

    for skill, stats in SKILLS["fighting"]["melee"].items():
        mdr = ArrangeToSkill(SKILLS["fighting"]["melee"][skill], arrange)

        lvl = Symbol('lvl')
        slv = solve(Bonus(lvl, *mdr) - 700)

        needed_level = ceiling(slv[0])

        if needed_level < meleeLevel:
            meleeSkill = skill
            meleeLevel = needed_level

    for skill, stats in SKILLS["fighting"]["defense"].items():
        mdr = ArrangeToSkill(SKILLS["fighting"]["defense"][skill], arrange)

        lvl = Symbol('lvl')
        slv = solve(Bonus(lvl, *mdr) - 600)

        needed_level = ceiling(slv[0])

        if needed_level < meleeLevel:
            defenseSkill = skill
            defenseLevel = needed_level

    fightingCosts = 0

    x = Symbol('x')
    fightingCosts += floor(integrate(XPCostFromPlayer(x), (x, 0, meleeLevel)))

    x = Symbol('x')
    fightingCosts += floor(integrate(XPCostFromPlayer(x), (x, 0, defenseLevel)))

    special = {}

    for method in [
        "tactics",
        "weapon",
    ]:
        skill = ArrangeToSkill(SKILLS["fighting"]["special"][method], arrange)

        lvl = Symbol('lvl')
        slv = solve(Bonus(lvl, *skill) - 500)

        needed_level = ceiling(slv[0])
        special[method] = int(needed_level)

        x = Symbol('x')
        fightingCosts += floor(integrate(XPCostFromPlayer(x), (x, 0, needed_level)))

    return {
        "fightingCosts": int(fightingCosts),
        "results": {
            meleeSkill: int(meleeLevel),
            defenseSkill: int(defenseLevel),
            "special": special,
        }
    }


EHA = [
    "dancing",
    "evoking",
    "channeling",
    "binding",
    "air",
    "chanting",
]

TPA = [
    "evoking",
    "air",
    "enchanting",
    "channeling",
    "chanting",
]

PFG = [
    "evoking",
    "channeling",
    "enchanting",
    "animating",
    "fire",
]

DKDD = [
    "dancing",
    "cursing",
    "summoning",
    "abjuring",
    "banishing"
]

ALL_METHODS = set(EHA + TPA + PFG + DKDD)

def totalMethodsCost(arrange):
    total_cost = 0
    methods = {
        "methods": {},
        "spells": {},
    }

    for method in ALL_METHODS:
        skill = ArrangeToSkill(SKILLS["methods"][method], arrange)

        lvl = Symbol('lvl')
        slv = solve(Bonus(lvl, *skill) - 500)

        neededLevel = ceiling(slv[0])
        methods["methods"][method] = int(neededLevel)

        x = Symbol('x')
        total_cost += floor(integrate(XPCostFromPlayer(x), (x, 0, neededLevel)))

    for method in [
        "offensive",
        "defensive",
    ]:
        skill = ArrangeToSkill(SKILLS["spells"][method], arrange)

        lvl = Symbol('lvl')
        slv = solve(Bonus(lvl, *skill) - 700)

        neededLevel = ceiling(slv[0])
        methods["spells"][method] = int(neededLevel)

        x = Symbol('x')
        total_cost += floor(integrate(XPCostFromPlayer(x), (x, 0, ceiling(slv[0]))))

    return {
        "methodsCosts": int(total_cost),
        "methods": methods,
    }


def computeCost(arrange):
    methodsResult = totalMethodsCost(arrange)
    fightingResult = findBestMelee(arrange)

    return {
        "total": int(methodsResult["methodsCosts"] + fightingResult["fightingCosts"]),
        "fighting": fightingResult,
        "methods": methodsResult,
    }



if __name__ == '__main__':
    # print(Bonus(300, 13, 13, 13, 13, 13))
    # print(GPRegen(13, 13, 13, 13, 13))
    #
    # lvl = Symbol('lvl')
    # slv = solve(Bonus(lvl, 13, 13, 13, 13, 13) - 307)
    # print(slv)
    # print(ceiling(slv[0]))
    # x = Symbol('x')
    # print(floor(integrate(XPCostFromPlayer(x), (x, 0, ceiling(slv[0])))))

    test = [i for i in range(10, 22)]
    possibles = [t for t in itertools.permutations(test, 5) if sum(t) == 65 and t[STR] >= 12 and t[INT] >= 14]

    best_arrange = [None] * 6

    arranges = []

    for arrange in list(possibles):
        mapo = ArrangeToSkill("IISWW", arrange)
        gpr = floor(GPRegen(*mapo))

        if gpr < 3:
            continue

        # if not best_arrange[gpr]:
        #     best_a

        costs = computeCost(arrange)
        if best_arrange[gpr] is None or best_arrange[gpr]["total"] is None:
            best_arrange[gpr] = costs

        arranges.append({
            "arrange": {
                "CON": arrange[CON],
                "DEX": arrange[DEX],
                "INT": arrange[INT],
                "STR": arrange[STR],
                "WIS": arrange[WIS],
            },
            "gpregen": int(gpr),
            "result": costs,
        })

        if best_arrange[gpr]["total"] > costs["total"]:
            best_arrange[gpr] = costs
            best_arrange[gpr]["arrange"] = arrange


    print(best_arrange)
    #print(arranges)
    print(json.dumps(arranges))
