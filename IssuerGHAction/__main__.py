#!/usr/bin/env python3

import typing
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from pprint import pprint

from dateutil.parser import parse as parseDate
from dateutil.relativedelta import relativedelta


try:
	from crontab import CronSlices
except:
	CronSlices = None


from . import *
from .Reaction import *

mdIndent = " " * 4  # markdown doesn't support tabs as indent
firstJoiner = "\n" + mdIndent + "* "
secondJoiner = "\n" + mdIndent * 2 + "* "


def labels2set(lblzList):
	return {lbl["name"] for lbl in lblzList}


actionsBotName = "github-actions"

def main():
	env = getGHEnv()
	gh = env["GITHUB"]
	inpV = env["INPUT"]
	e = json.loads(gh["EVENT_PATH"].read_text())
	rol, rn = gh["REPOSITORY"].split("/")

	api = GHAPI(inpV["GITHUB_TOKEN"])
	orgO = api.org(rol)
	repO = api.repo(rol, rn)
	cfg = parseConfig(Path(inpV["CONFIG"]))

	tp = gh["EVENT_NAME"]
	if tp == "issues":
		issue(repO, orgO, cfg, e["issue"])
	elif tp == "schedule":
		schedule(repO, orgO, cfg, e["schedule"])
	else:
		raise KeyError(tp)


class Shit:
	__slots__ = ("react", "namespace", "issueO", "userName", "lblz", "checkboxesLabelsAll", "created", "modified", "events", "baseTime", "markerLabel", "cleanedLabels", "lblzMustBe", "invalidLabel", "validLabel", "delayedActionLabel", "wasInvalid", "wasValid")

	def __init__(self, repO, cfg, i):
		self.events = None
		self.baseTime = None

		id = i["id"]
		no = i["number"]
		b = i["body"]
		l = i["locked"]
		self.created = parseDate(i["created_at"])
		self.modified = parseDate(i["updated_at"])
		user = i["user"]
		self.userName = user["login"]
		self.lblz = labels2set(i["labels"])
		self.issueO = repO.issue(no)

		markerLabels = set(cfg["templates"])
		currentIssueMarkerLabels = markerLabels & self.lblz
		if not currentIssueMarkerLabels:
			sys.exit(0)

		self.react = Reaction()

		if len(currentIssueMarkerLabels) > 1:
			self.react.issues += ["Conflicting marker labels!"]
			self.checkboxesLabelsAll = set()
			for currentLabelDtor in cfg["templates"]:
				self.checkboxesLabelsAll |= currentLabelDtor["checkboxesLabelsAll"]
			self.namespace = cfg
		else:
			self.markerLabel = next(iter(currentIssueMarkerLabels))
			currentLabelDtor = cfg["templates"][self.markerLabel]
			self.namespace = currentLabelDtor
			self.checkboxesLabelsAll = currentLabelDtor["checkboxesLabelsAll"]

			b = normalize(unicodeNormalization, b)
			parsed = parseCheckboxedTemplate(b, currentLabelDtor["cbxSections"])
			#currentLabelDtor
			#print(parsed[0])

			lint(parsed, currentLabelDtor, self.react)
			applyTimedOutActions(currentLabelDtor, self.react, "**issue**")

		delayedActionLabel = self.namespace["essentialLabels"]["delayedAction"]
		self.cleanedLabels = self.lblz - self.checkboxesLabelsAll - {delayedActionLabel}

		self.react.finalize()
		slblz = self.namespace["essentialLabels"]
		self.invalidLabel = slblz["invalid"]
		self.validLabel = slblz["valid"]
		self.delayedActionLabel = slblz["delayedAction"]

		self.wasInvalid = self.invalidLabel in self.lblz
		self.wasValid = self.validLabel in self.lblz

		if self.react.issues:
			self.lblzMustBe = (self.cleanedLabels | {self.invalidLabel}) - {self.validLabel}
		else:
			self.lblzMustBe = (self.react.labels2assign | self.cleanedLabels | {self.validLabel}) - {self.invalidLabel}

	def finalizeDelayed(self):
		self.events = self.issueO.getEvents()
		self.baseTime = self.getBaseTime()
		self.react.finalizeDelayed(self.baseTime)


	def getBaseTime(self):
		for e in self.events:
			if e["actor"]["login"] == actionsBotName:
				if "labels" in e and self.delayedActionLabel in labels2set(e["labels"]):
					return parseDate(e["created_at"])
		return self.created


	def doTimedoutActionsForIssue(self, orgO, repO) -> bool:
		now = datetime.now(timezone.utc)
		if self.react.closeAfterTime is not None:
			if now >= self.react.closeAfterTime:
				self.issueO.close()  # todo: do automatic reopening
				self.issueO.setLabels(self.lblzMustBe)

		if self.react.blockAfterTime is not None and now >= self.react.blockAfterTime:
			#repO.expell(userName)
			orgO.block(userName)
		if self.react.deleteAfterTime is not None and now >= self.react.deleteAfterTime:
			self.issueO.delete()
			return False
		return True

	def generateIssuesMessage(self, key):
		templ = self.namespace["messages"][key]
		res = templ.format(userName="@" + self.userName, count=len(self.react.issues))
		res += firstJoiner + firstJoiner.join(self.react.issues)
		return res


def schedule(repO, orgO, cfg, schedCfg: str):
	if CronSlices:
		schedCfg = CronSlices(schedCfg)
		print(schedCfg)

	delayedActionLabel = cfg["essentialLabels"]["delayedAction"]
	# todo: replace with GraphQL
	issz = repO.getIssues(labels=delayedActionLabel, state=("open" if True else "all")) # todo OR all the templates dtors and use `all` only if needed to delete issues
	for i in issz:
		pp = Shit(repO, cfg, i)
		pp.finalizeDelayed()
		pp.doTimedoutActionsForIssue(orgO, repO)


def issue(repO, orgO, cfg, i):
	pp = Shit(repO, cfg, i)
	slblz = pp.namespace["essentialLabels"]
	msgz = pp.namespace["messages"]
	delayedActionLabel = slblz["delayedAction"]

	if pp.react.issues:
		delActs = bool(tuple(pp.react.iterateDelayedActions()))
		if delActs:
			pp.finalizeDelayed()

		if not pp.wasInvalid:
			commentText = pp.generateIssuesMessage("greeting")
			if delActs:
				commentText += (
					"\n" + "Your issue gonna be " +
					", ".join((cfgK + "d at " + str(time) + "( in " + fancifyTime(relativedelta(time, pp.baseTime).normalized()) + " since " + str(pp.baseTime) + ")") for cfgK, propN, time in pp.react.iterateDelayedActions()) +
					" if not fixed untill that time."
				)
				pp.lblzMustBe |= {pp.delayedActionLabel}
		else:
			# todo: parse the issues and diff them
			commentText = pp.generateIssuesMessage("issuesStillPresent")
		pp.issueO.leaveAComment(commentText)
	else:
		if pp.wasInvalid or not pp.wasValid:
			pp.issueO.leaveAComment(pp.generateIssuesMessage("issuesFixed"))
		else:
			pass  # everything is OK

	if delActs:
		issueStillExists = pp.doTimedoutActionsForIssue(orgO, repO)
	if issueStillExists and pp.lblzMustBe != pp.lblz:
		pp.issueO.setLabels(pp.lblzMustBe)


if __name__ == "__main__":
	main()
