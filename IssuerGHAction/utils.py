import typing
from pathlib import Path
from unicodedata import normalize


def fancifyTime(ft):
	res = (str(ft.years) + " Y, " if ft.years else "") + (str(ft.months) + " M, " if ft.months else "") + (str(ft.days) + " D, " if ft.days else "") + (str(ft.hours) + " h, " if ft.hours else "") + (str(ft.minutes) + " m, " if ft.minutes else "") + (str(ft.seconds) + " s, " if ft.seconds else "")
	if not res:
		res = "immediately"
	return res


class ClassDictMeta(type):
	def __new__(cls, className: str, parents, attrs: typing.Dict[str, typing.Any], *args, **kwargs):
		newAttrs = type(attrs)(attrs)
		return {k: v for k, v in newAttrs.items() if k[0] != "_"}


inf = float("inf")


def linesSet(s: str):
	linesSet = set()
	for l in s.splitlines():
		l = l.strip()
		if l:
			linesSet |= {l}
	return linesSet


unicodeNormalization = "NFKD"
