import math

pows = """
thousand
million
billion
trillion
quadrillion
quintillion
sextillion
septillion
octillion
nonillion
decillion
undecillion
duodecillion
tredecillion
quattuordecillion
quindecillion
sexdecillion
septendecillion
octodecillion
novemdecillion
vigintillion
unvigintillion
duovigintillion
trevigintillion
quattuorvigintillion
quinvigintillion
sexvigintillion
septenvigintillion
octovigintillion
novemvigintillion
trigintillion
untrigintillion
duotrigintillion
tretrigintillion
quattuortrigintillion
quintrigintillion
sextrigintillion
septentrigintillion
octatrigintillion
novemtrigintillion
quadragintillion
""".split()

nums = """
zero
one
two
three
four
five
six
seven
eight
nine
ten
eleven
twelve
thirteen
fourteen
fifteen
sixteen
seventeen
eighteen
nineteen
""".split()

tens = """
ten
twenty
thirty
fourty
fifty
sixty
seventy
eighty
ninety
""".split()


def fmt_unit(x: int, single=False) -> list[str]:
    if x == 0 and not single:
        return []

    return [nums[x]]


def fmt_tens(x: int) -> list[str]:
    ans: list[str] = []
    if x >= 20:
        ans.append(tens[x // 10 - 1])
        x -= (x // 10) * 10
        if x > 0:
            ans += fmt_unit(x)
    else:
        ans += fmt_unit(x)
    return ans


def fmt_hundreds(x: int) -> list[str]:
    ans: list[str] = []
    if x < 100:
        ans = fmt_tens(x)
    else:
        ans += fmt_unit(x // 100)
        ans += ["hundred"]
        x -= (x // 100) * 100
        ans += fmt_tens(x)
    return ans


def fmt_num(x: int) -> list[str]:
    ans: list[str] = []
    p: int = math.ceil(math.log10(x) // 3) * 3
    while p >= 3:
        val = x // (10**p)
        if val > 0:
            ans += fmt_hundreds(val)
            ans += [pows[p // 3 - 1]]
        x -= val * 10**p
        p -= 3
    ans += fmt_hundreds(x)
    return ans


i = int(input())
print(" ".join(fmt_num(i)))
