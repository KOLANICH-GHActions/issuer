import typing
import re
from urllib.parse import urlparse

from .parsers import node2text
from .Reaction import *
from .utils import *


def applyTimedOutActions(reactionDtor, react: Reaction, reason: str):
	for toConfN, toAcN in timeoutActions():
		if toConfN in reactionDtor:
			prevV = getattr(react, toAcN)
			if prevV is None:
				prevV = inf
			to = reactionDtor[toConfN]
			setattr(react, toAcN, min(to, prevV))
			react.issues.append("`" + str(reason) + "` is invalid: will be " + toConfN + "d in `" + str(to) + "` seconds")


def lintCheckboxSections(sections, sectionsDtors, react: Reaction):
	for sN, sd in sectionsDtors.items():
		reactionDtor = sd["react"]
		shouldAssign = bool(reactionDtor["assign"]) if "assign" in reactionDtor else False
		checked = 0
		if sN not in sections:
			if sd["min"] >= 0:
				issues.append("Mandatory section `" + sN + "` is missing.")
			continue
		cbxses = sections[sN]
		issues = []
		for i, (cN, cbx) in enumerate(cbxses.items()):
			if cN not in sd["allowed"]:
				issues.append("Forbidden `" + str(i) + "`-th label in `" + sN + "`")
			if cbx.checked:
				checked += 1
				if shouldAssign:
					react.labels2add.append(cN)
		if checked < sd["min"]:
			issues.append("At least `" + str(sd["min"]) + "` elements in `" + sN + "` are required")
		if checked > sd["max"]:
			issues.append("Maximum `" + str(sd["max"]) + "` elements in `" + sN + "` are allowed")
		react.issues += issues
		if issues:  # if invalid
			applyTimedOutActions(reactionDtor, react, sN)


def lintRestSections(sections, sectionsDtors, react):
	for sN, sd in sectionsDtors.items():
		if sN not in sections:
			react.issues.append("Mandatory section `" + sN + "` is missing.")
			continue
		sec = sections[sN]
		secText = node2text(sec).strip()
		ls = linesSet(secText)
		linesNotRemoved = ls & sd["default"]
		if linesNotRemoved and sd["mustRemoveTemplate"]:
			react.issues.append("You must remove all the template traces from the section `" + sN + "`")


def lint(parsed, currentLabelCfg, react):
	restSections, cbxSections = parsed
	lintCheckboxSections(cbxSections, currentLabelCfg["cbxSections"], react)
	lintRestSections(restSections, currentLabelCfg["restSections"], react)
