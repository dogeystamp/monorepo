from number_speller import fmt_num

for i in range(int(3e5)):
    print(f"\tcase {i}:")
    print(f'\t\tprintf("{' '.join(fmt_num(i))}");')
    print(f"\t\tbreak;")
