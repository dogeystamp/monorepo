# self-explanatory by looking at the output

def digs(x: int) -> list[int]:
    return [int(i) for i in str(x)]

def outp(x: int, exp: int) -> None:
    pw: int = x**exp
    print(f"{exp}√{pw}: {' + '.join(str(pw))} = {(s := sum(digs(pw)))}\n\t{s} - {exp} = {x} ✓\n")

for exp in range(1, 10):
    gen = (i for i in range(10000) if sum(digs(i**exp)) - exp == i)
    for x in gen:
        outp(x, exp)
