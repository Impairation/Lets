import os
import subprocess
from pp import omppc

from common import generalUtils
from common.constants import bcolors
from common.ripple import scoreUtils
from constants import exceptions
from helpers import consoleHelper
from helpers import osuapiHelper
from objects import glob
from common.log import logUtils as log
from helpers import mapsHelper

# constants
MODULE_NAME = "omppcPy"
UNIX = True if os.name == "posix" else False

def fixPath(command):
	"""
	Replace / with \ if running under WIN32

	commnd -- command to fix
	return -- command with fixed paths
	"""
	if UNIX:
		return command
	return command.replace("/", "\\")

class piano:
	"""
	Oppai calculator
	"""
	# Folder where oppai is placed
	OPPAI_FOLDER = "../lets/omppc"

	def __init__(self, __beatmap, __score = None, acc = 0, mods = 0, tillerino = False, stars = False):
		"""
		Set oppai params.

		__beatmap -- beatmap object
		__score -- score object
		acc -- manual acc. Used in tillerino-like bot. You don't need this if you pass __score object
		mods -- manual mods. Used in tillerino-like bot. You don't need this if you pass __score object
		tillerino -- If True, self.pp will be a list with pp values for 100%, 99%, 98% and 95% acc. Optional.
		stars -- If True, self.stars will be the star difficulty for the map (including mods)
		"""
		# Default values
		self.pp = 0
		self.stars = 0
		self.score = None
		self.acc = acc
		self.mods = mods
		self.beatmap = __beatmap
		self.map = "{}.osu".format(self.beatmap.beatmapID)

		if __score is not None:
			self.score = __score
			self.acc = self.score.accuracy*100
			self.mods = self.score.mods
		self.getPP(tillerino, stars)

	def getPP(self, tillerino=False, stars=False):
		"""
		Calculate total pp value with oppai and return it

		return -- total pp
		"""
		# Set variables
		self.pp = 0
		self.stars = 0
		try:
			# Build .osu map file path
			mapFile = "/data/oppai/maps/{map}".format(map=self.map)

			mapsHelper.cacheMap(mapFile, self.beatmap)

			# Base command

			if tillerino == True:
				pp_list = []
				for acc in [100, 99, 98, 95]:
					calc = omppc.Calculator(mapFile, score=1000000, mods=self.mods, accuracy=acc)
					pp = calc.calculate_pp()[0]
					pp_list.append(round(pp, 2))	
			else:
				calc = omppc.Calculator(mapFile, score=(self.score.score if self.score is not None else 1000000), mods=self.mods, accuracy=self.acc)
				pp = calc.calculate_pp()[0]			
			if stars == True:
				self.stars = round(calc.calculate_stars(),5)
			consoleHelper.printRippoppaiMessage("calculated pp {}".format(pp))
			if(tillerino == True):
				self.pp = pp_list
			else:
				self.pp = round(pp,2)
		finally:
			return self.pp
