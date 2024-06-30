from num2words import num2words

def number_to_words(num):
    gerundete_zahl = round(float(num), 2)

    parts = str(gerundete_zahl).split(".")
    integer_part = int(parts[0])
    decimal_part = parts[1] if len(parts) > 1 else "00"

    words = num2words(integer_part, lang='de')

    if decimal_part != "00":
        decimal_words = " Komma " + " ".join(num2words(int(digit), lang='de') for digit in decimal_part)
        words += decimal_words

    return words