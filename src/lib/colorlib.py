def hsl_to_rgb(h: int, s: float, l: float):
    def _hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        elif t > 1:
            t -= 1

        if (t * 6) < 1:
            return p + (q - p) * 6 * t
        if (t * 2) < 1:
            return q
        if (t * 3) < 2:
            return p + (q - p) * (2/3 - t) * 6
        return p

    r = g = b = 0

    if s == 0:
        r = g = b = l
    else:
        if l < 0.5:
            q = l * (1 + s)  # temporary_1
        else:
            q = (l + s) - (l * s)  # temporary_1

        p = (2 * l) - q  # temporary_2

        h /= 360

        r = _hue_to_rgb(p, q, h + (1/3))
        g = _hue_to_rgb(p, q, h)
        b = _hue_to_rgb(p, q, h - (1/3))

    return round(r*255), round(g*255), round(b*255)


def rgb_to_hsl(r: int, g: int, b: int):
    h = s = l = 0.0

    r, g, b = [x/255 for x in (r, g, b)]

    minimum = min(r, g, b)
    maximum = max(r, g, b)

    l = (minimum+maximum)/2

    if not minimum == maximum:  # not achromatic
        d = maximum - minimum
        s = (d / (2.0 - d) if l > 0.5 else d / (maximum + minimum))

        h = {
            r: (g-b) / d + (6.0 if g < b else 0),
            g: (b-r) / d + 2.0,
            b: (r-g) / d + 4.0
        }[maximum]

        h *= 60

    return round(h), round(s, 2), round(l, 2)


def rgb_to_hex(r, g, b):
    return("%0.2X%0.2X%0.2X" % (r, g, b))


def hsl_to_hex(h, s, l):
    return rgb_to_hex(*hsl_to_rgb(h, s, l))


def brightness_to_pwm_duty(pwm_max: int):
    def inner(val: int) -> int:
        return int(abs((val * pwm_max/255)))
    return inner
