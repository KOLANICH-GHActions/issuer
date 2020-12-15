import re
import typing
from copy import deepcopy
from pathlib import Path
from xml.dom.minidom import Element
from warnings import warn

import commonmark
import recommonmark
from recommonmark.parser import CommonMarkParser

import docutils
import docutils.frontend

from ruamel.yaml import YAML

from .utils import *


leadingTabsRx = re.compile("^( *)(\\t+)")
parser = YAML(typ="safe")

def _tabbedYaml2YamlReplacer(m):
	return m.group(1) + "  " * len(m.group(2))

def _tabbedYaml2Yaml(text):
	for l in text.splitlines():
		yield leadingTabsRx.sub(_tabbedYaml2YamlReplacer, l)

def tabbedYaml2Yaml(text):
	return "\n".join(_tabbedYaml2Yaml(text))

def parseYaml(text):
	return parser.load(tabbedYaml2Yaml(text))

thisDir = Path(__file__).parent.absolute()
schemaFile = thisDir / "issuer.schema.yaml"
schema = parseYaml(schemaFile.read_text(encoding="utf-8"))

defaultSectionCfg = schema["properties"]["react"]["default"]
defaultRestSectionCfg = {"mustRemoveTemplate": True}

defaultCfg = {
	"essentialLabels": {
		"invalid": schema["defs"]["essentialLabels"]["properties"]["invalid"]["default"],
		"valid": schema["defs"]["essentialLabels"]["properties"]["valid"]["default"],
		"delayedAction": schema["defs"]["essentialLabels"]["properties"]["delayedAction"]["default"]
	},
	"messages": {
		"greeting": schema["defs"]["messagesTemplates"]["properties"]["greeting"]["default"],
		"issuesFixed": schema["defs"]["messagesTemplates"]["properties"]["issuesFixed"]["default"],
		"issuesStillPresent": schema["defs"]["messagesTemplates"]["properties"]["issuesStillPresent"]["default"],
	},
}

defaultCfg.update(defaultSectionCfg)
defaultCfg.update(defaultRestSectionCfg)

issuesTemplatesPrefix = Path(".") / ".github" / "ISSUE_TEMPLATE"


def deepMerge(src, dst, propagatingProps=None):
	if propagatingProps is None:
		propagatingProps = src

	for n in propagatingProps:
		if n not in src:
			continue
		v = src[n]
		if n not in dst:
			dst[n] = deepcopy(v)
		else:
			v1 = dst[n]
			if isinstance(v1, dict):
				deepMerge(v, v1, propagatingProps[n])
			else:
				dst[n] = deepcopy(v)


templateMetadataBlockRegEx = re.compile("^(-{3,})(\\r?\\n)(.+)\\2\\1\\2", re.DOTALL)
def parseTemplateMetadataBlock(t: str, fileName: Path):
	m = templateMetadataBlockRegEx.match(t)
	if not m:
		raise ValueError("Metadata block is not detected in the issue template", fileName)
	
	metadataBlockYamlText = m.group(3)
	try:
		return parser.load(metadataBlockYamlText)
	except:
		raise ValueError("Incorrect YAML in metadata block", fileName)
	

def parseConfig(path: Path = "./.github/issuer.yml"):
	path = Path(path)
	t = normalize(unicodeNormalization, path.read_text())
	cfg = parser.load(t)

	deepMerge(defaultCfg, cfg, defaultCfg)
	cfg["templates"] = templatesDst = {}
	
	for templateFile in issuesTemplatesPrefix.glob("*.md"):
		templateText = templateFile.read_text(encoding="utf-8")
		try:
			templateMetadataYaml = parseTemplateMetadataBlock(templateText, templateFile)
		except:
			warn(str(templateFile) + " has invalid metadata block, skipping")
			continue
		
		if "issuer" not in templateMetadataYaml:
			continue
		
		templDtor = templateMetadataYaml["issuer"]
		templ = parseMarkdown(templateText)
		templDtor["file"] = templateFile
		
		templateLabels = templateMetadataYaml["labels"]
		if isinstance(templateLabels, str):
			issueLabel = templateLabels
		elif isinstance(templateLabels, list):
			issueLabel = templateLabels[0]
		
		if issueLabel in templatesDst:
			raise KeyError("Conflicting labels: " + str(templateFile) + ", " + str(templatesDst[issueLabel]["file"]))
		
		templatesDst[issueLabel] = templDtor

		deepMerge(cfg, templDtor, defaultCfg)

		secsDtors = templDtor["cbxSections"]
		checkboxesLabelsAll = set()
		restSections, cbxses = parseCheckboxedTemplate(templ, checkboxSectionsNames=secsDtors)
		for sn, cbxses in cbxses.items():
			secDtor = secsDtors[sn]
			allowed = set(cbxses)
			secDtor["allowed"] = allowed
			checkboxesLabelsAll |= allowed

			if "min" not in secDtor or secDtor["min"] is None:
				secDtor["min"] = 0
			if "max" not in secDtor or secDtor["max"] is None:
				secDtor["max"] = inf
			deepMerge(templDtor, secDtor, defaultSectionCfg)

		if "restSections" not in templDtor:
			templDtor["restSections"] = rSDtor = {}
		else:
			rSDtor = templDtor["restSections"]

		for sn, s in restSections.items():
			if sn not in rSDtor:
				rSDtor[sn] = sD = {}
			else:
				sD = rSDtor[sn]
			sD["default"] = linesSet(node2text(s))
			deepMerge(templDtor, sD, defaultRestSectionCfg)

		templDtor["checkboxesLabelsAll"] = checkboxesLabelsAll

	return cfg


def parseMarkdown(t: typing.Union[str, Path]):
	if isinstance(t, Path):
		t = t.read_text(encoding="utf-8")
	s = docutils.frontend.OptionParser(components=(CommonMarkParser,)).get_default_values()
	p = CommonMarkParser()
	doc = docutils.utils.new_document(None, s)
	p.parse(t, doc)
	parsedDocs = doc.asdom()
	doc = next(iter(parsedDocs.childNodes))
	return doc


def getTextFromNodes(node):
	if node.nodeType == node.TEXT_NODE:
		yield node.data
	else:
		for cn in node.childNodes:
			yield from getTextFromNodes(cn)


def node2text(node):
	return "".join(getTextFromNodes(node))


def getSections(doc):
	res = {}
	for s in doc.getElementsByTagName("section"):
		titleCand = s.firstChild
		if titleCand.tagName == "title":
			if s.getElementsByTagName("section"):
				continue
			name = node2text(titleCand).strip()
			res[name] = s
	return res


class Checkbox:
	__slots__ = ("name", "checked", "desc", "pNode", "liNode")

	def __init__(self, name, checked, desc, liNode, pNode):
		self.name = name
		self.checked = checked
		self.desc = desc
		self.liNode = liNode
		self.pNode = pNode

	def __repr__(self):
		return self.__class__.__name__ + "<" + ", ".join(repr(getattr(self, k)) for k in self.__class__.__slots__[:3]) + ">"


cbxRx = re.compile("^\\[([ xXvV])\\]\\s+(.+)$")


def extractCheckboxes(sec):
	res = {}
	lists = list(sec.getElementsByTagName("bullet_list"))
	if len(lists) != 1:
		raise ValueError()
	l = lists[0]

	for i in l.getElementsByTagName("list_item"):
		if len(i.childNodes) != 1:
			raise ValueError()
		p = i.firstChild
		if p.tagName != "paragraph":
			raise ValueError()
		v = node2text(p)
		m = cbxRx.match(v)
		if not m:
			raise ValueError()
		c, lbl = m.groups()
		cbxV = c != " "
		lblSpl = lbl.split(" - ", 1)
		k = lblSpl[0].strip()
		if len(lblSpl) > 1:
			desc = lblSpl[1].strip()
		else:
			desc = None
		res[k] = Checkbox(k, cbxV, desc, i, p)
	return res


def separateCheckboxSections(sections, checkboxSectionsNames):
	res = {}
	for cbxSName in checkboxSectionsNames:
		res[cbxSName] = extractCheckboxes(sections[cbxSName])
		del sections[cbxSName]
	return res


def parseCheckboxedTemplate(src: typing.Union[str, Path, Element], checkboxSectionsNames: typing.Iterable[str]):
	if not isinstance(src, Element):
		doc = parseMarkdown(src)
	else:
		doc = src
	sections = getSections(doc)
	checkboxesSections = separateCheckboxSections(sections, checkboxSectionsNames)
	return sections, checkboxesSections
