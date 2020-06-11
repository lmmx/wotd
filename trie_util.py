def mask_preceding(preceder, seen):
    ppreceder = " ⇒ ".join(preceder)
    pseen = " ⇢ ".join(seen[len(preceder) :])
    str_out = " ⠶ ".join([ppreceder, pseen])
    return str_out
