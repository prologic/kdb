# Filename: host.py
# Module:	host
# Date:		30th June 2006
# Author:	James Mills, prologic at shortcircuit dot net dot au

"""Host Tools

This plugin provides various tools to work with
hostnames and ip addresses.
"""

__ver__ = "0.0.1"
__author__ = "James Mills, prologic at shortcircuit dot net dot au"

import string
import socket

from kdb.plugin import BasePlugin

class Host(BasePlugin):
	"Host Tools"

	def cmdHOST(self, source, host):
		"""Resolve the given hostname/ip
		
		Syntax: HOST <hostname/ip>
		"""

		isIP = True
		for c in host.replace(".", ""):
			if c not in string.digits:
				isIP = False
				break

		if isIP:
			try:
				name, aliases, addresses = socket.gethostbyaddr(
						host)
				msg = "%s -> %s" % (host, name)
			except socket.gaierror, e:
				msg = "%s -> %s" % (host, e[1])
			except socket.herror, e:
				msg = "%s -> %s" % (host, e[1])
		else:
			try:
				address = socket.gethostbyname(host)
				msg = "%s -> %s" % (host, address)
			except socket.gaierror, e:
				msg = "%s -> %s" % (host, e[1])

		return msg
