import typing
from urllib.parse import urljoin, urlencode

#gh api not working this way
#import certifi
#from urllib3 import PoolManager
#import urllib3.contrib.pyopenssl
#urllib3.contrib.pyopenssl.inject_into_urllib3()
#certsStore = certifi.where()
#http = PoolManager(ca_certs=certsStore, cert_reqs="CERT_REQUIRED")
import requests

try:
	import ujson as json
except ImportError:
	import json


GH_API_BASE = "https://api.github.com/"


class GHApiObj_:
	__slots__ = ()

	@property
	def prefix(self) -> str:
		raise NotImplementedError()

	def req(self, path, obj, method="post"):
		raise NotImplementedError()


class GHAPI(GHApiObj_):
	__slots__ = ("hdrz",)

	def __init__(self, token, userAgent=None):
		self.hdrz = {
			"Authorization": "Bearer " + token,
			"Content-Type": "application/json",
			"Accept": "application/vnd.github.raw+json"
		}
		if userAgent:
			hdrz["User-Agent"] = userAgent

	@property
	def prefix(self) -> str:
		return GH_API_BASE

	def req(self, path, obj, method="post", previews=()):
		if path[-1] == "/":
			path = path[:-1]
		method = method.upper()
		hdrz = type(self.hdrz)(self.hdrz)
		if previews:
			hdrz["Accept"] = ", " + (", ".join(("application/vnd.github." + preview + "-preview") for preview in previews))

		#res = http.request(method, self.prefix + path, body=json.dumps(obj).encode("utf-8") if obj is not None else b"", headers=hdrz)
		res = requests.request(method, self.prefix + path, data=json.dumps(obj) if obj is not None else None, headers=hdrz)
		#return res.data.decode("utf-8")
		res.raise_for_status()
		return res

	def repo(self, owner: str, repo: str):
		return Repo(self, owner, repo)

	def org(self, owner: str):
		return Org(self, owner)


class GHApiObj(GHApiObj_):
	__slots__ = ("parent",)

	def __init__(self, parent):
		self.parent = parent

	def req(self, path, obj, method="post", previews=()):
		return self.parent.req(self.prefix + path, obj, method=method, previews=previews)


class Repo(GHApiObj):
	__slots__ = ("owner", "repo")

	def __init__(self, parent, owner: str, repo: str):
		super().__init__(parent)
		self.owner = owner
		self.repo = repo

	@property
	def prefix(self) -> str:
		return "repos/" + self.owner + "/" + self.repo + "/"

	def issue(self, no: int):
		return Issue(self, no)

	def expell(self, user: str):
		self.req("collaborators/" + user, None, method="delete", previews=("inertia",))

	def getIssues(self, labels:typing.Optional[str]=None, state:typing.Optional[str]=None):
		q = {}
		if labels is not None:
			if not isinstance(labels, str):
				labels = ",".join(labels)
			q["labels"] = labels
		if state is not None:
			q["state"] = state
		return self.req("issues?" + urlencode(q), None, method="get", previews=("machine-man",)).json()


class Issue(GHApiObj):
	__slots__ = ("no",)

	def __init__(self, parent, no: int):
		super().__init__(parent)
		self.no = no

	@property
	def prefix(self) -> str:
		return "issues/" + str(self.no) + "/"

	def leaveAComment(self, body: str):
		self.req("comments", {"body": str(body)})

	def setLabels(self, labels: typing.Iterable[str]):
		self.req("labels", {"labels": list(labels)}, method="put")

	def patch(self, patch: typing.Mapping[str, typing.Any]):
		self.req("", patch, method="patch")

	def close(self):
		self.patch({"state": "closed"})

	def open(self):
		self.patch({"state": "open"})

	def delete(self):
		self.req("", None, method="delete")

	def lock(self, reason: str = None):
		self.req("lock", {"lock_reason": reason} if reason else None, method="put", previews=("sailor-v",))

	def unlock(self):
		self.req("lock", None, method="delete", previews=("sailor-v",))

	def react(self, reaction: str):
		self.req("reactions", {"content": reaction}, method="put", previews=("sailor-v",))

	def getEvents(self):
		return self.req("events", None, method="get", previews=("sailor-v", "starfox")).json()


class Org(GHApiObj):
	__slots__ = ("name",)

	def __init__(self, parent, name: str):
		super().__init__(parent)
		self.name = name

	@property
	def prefix(self) -> str:
		return "orgs/" + str(self.name) + "/"

	def block(self, user: str):
		self.req("blocks/" + user, None, method="put", previews=("giant-sentry-fist",))

	def unblock(self, user: str):
		self.req("blocks/" + user, None, method="delete", previews=("giant-sentry-fist",))
