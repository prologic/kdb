# Filename: core.py
# Module:	core
# Date:		2nd August 2005
# Author:	James Mills, prologic at shortcircuit dot net dot au

"""core

This is the core of kdb.
"""

import os
import signal
import socket
from traceback import format_exc

from pymills.utils import State
from pymills.event import Component, filter, listener

from bot import Bot

class Core(Component):

	def __init__(self, event, env):
		self.env = env

		if os.name in ["posix", "mac"]:
			signal.signal(signal.SIGHUP, self.rehash)
			signal.signal(signal.SIGTERM, self.term)

		# Initialize

		self.bot = Bot(self.env.event, self.env)
		self.env.loadPlugins(self.bot)

		self.running = True
		self.state = State()

	# Service Commands

	@listener("term")
	def term(self, signal=0, stack=0):
		self.bot.ircQUIT("Received SIGTERM, terminating...")
		self.state.set("TERMINATING")
	
	@listener("rehash")
	def rehash(self, signal=0, stack=0):
		self.env.reload()
	
	@filter()
	def onDEBUG(self, event):
		self.env.log.debug(event)
		return False, event

	@listener("timer:reconnect")
	def onRECONNECT(self, n, host, port, ssl, auth):
		env = self.env
		bot = self.bot

		self.state.set("CONNECTING")

		bot.open(host, port, ssl)

	def run(self):
		env = self.env
		event = env.event
		timers = env.timers
		bot = self.bot

		host = env.config.get("connect", "host")
		port = env.config.getint("connect", "port")

		auth = {
				"password": env.config.get("connect", "password"),
				"ident": env.config.get("bot", "ident"),
				"nick": env.config.get("bot", "nick"),
				"name": env.config.get("bot", "name"),
				"server": env.config.get("connect", "host"),
				"host": socket.gethostname()
				}

		self.state.set("CONNECTING")

		if self.env.config.has_option("connect", "ssl"):
			ssl = self.env.config.getboolean("connect", "ssl")
		else:
			ssl = False

		bot.open(host, port, ssl)
		if bot.connected:
			bot.connect(auth)

		while self.running:

			try:
				if bot.connected:
					bot.process()
				else:
					if self.state == "TERMINATING":
						self.running = False
					elif not self.state == "WAITING":
						self.state.set("DISCONNECTED")

				if self.state == "CONNECTING":
					if bot.connected:
						self.state.set("CONNECTED")
				elif self.state == "CONNECTED":
					self.state.set("AUTHENTICATED")
					bot.connect(auth)
				elif self.state == "DISCONNECTED":
					self.state.set("WAITING")
					env.log.info(
							"kdb was disconnected, "
							"Reconnecting in 60s...")
					self.env.timers.add(
							60,
							channel="timer:reconnect",
							host=host, port=port, ssl=ssl, auth=auth)

				timers.process()
				event.flush()
			except KeyboardInterrupt:
				self.term()
			except Exception, e:
				if e[0] == 4:
					self.term()
				else:
					self.env.errors += 1
					self.env.log.error("Error occured: %s" % e)
					self.env.log.error(format_exc())

		for i in xrange(len(event)):
			event.flush()

		self.env.unloadPlugins()
