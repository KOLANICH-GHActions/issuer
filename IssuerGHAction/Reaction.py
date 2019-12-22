import typing
from datetime import datetime, timedelta

_timeoutActions = ("delete", "close", "block")


def timeoutActions():
	for f in _timeoutActions:
		yield (f, f + "AfterTime")


def selectSecondSubitems(it):
	for e in it:
		yield e[1]


class Reaction:
	__slots__ = ("labels2assign", "reactions2apply", "issues", *selectSecondSubitems(timeoutActions()))

	def __init__(self):
		self.labels2assign = []
		self.reactions2apply = []
		self.issues = []
		for n in selectSecondSubitems(timeoutActions()):
			setattr(self, n, None)

	def finalize(self):
		self.labels2assign = set(self.labels2assign)

	def finalizeDelayed(self, timeoutBase: datetime):
		for cfgN, n, v in self.iterateDelayedActions():
			v = getattr(self, n)
			if v is not None:
				setattr(self, n, timeoutBase + timedelta(seconds=v))

	def iterateDelayedActions(self):
		for cfgK, attrN in timeoutActions():
			v = getattr(self, attrN)
			if v is not None:
				yield (cfgK, attrN, v)
