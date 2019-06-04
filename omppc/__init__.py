from lupa import LuaRuntime

# Create lua runtime
lua = LuaRuntime()

# Import all needed lua packages
lua.require("omppc.tweaks.tweaks")
lua.require("omppc.Mods")
lua.require("omppc.Note")
lua.require("omppc.Beatmap")
lua.require("omppc.PerformanceCalculator")
lua.require("omppc.PlayData")

# Lua function wrappers
_lua__set_play_data = lua.eval("""
function(beatmap, score, mods, accuracy)
	score = score or 1000000
	mods = mods or 0
	accuracy = accuracy or 1

	playData = PlayData:new()
	playData.mods = Mods:new():parse(mods)

	playData.beatmap = Beatmap:new()
	playData.beatmap:parse(beatmap)
	playData.beatmap.mods = playData.mods

	playData.score = score
	playData.accuracy = accuracy

	return playData
end
""")

_lua__get_performance_points = lua.eval("""
function(playData)
	return playData:getPerformancePoints(), playData.pCalc.strainValue, playData.pCalc.accValue
end
""")

_lua__get_star_rate = lua.eval("""
function(playData)
	return playData.beatmap:getStarRate()
end
""")

# omppc Python class
class Calculator:
	"""
	omppc python wrapper
	"""
	__slots__ = ["_play_data", "_beatmap_path", "_score", "_mods", "_accuracy"]

	def __init__(self, beatmap_path, score=1000000, mods=0, accuracy=100, accuracy_percentage=True):
		"""
		Initializes an omppc object

		:param beatmap_path: path of .osu file. Required.
		:param score: score points (0 ~ 1000000). Default: 1000000
		:param mods: mods flags. Supported: 1, 2, 64, 256 (respectively NF, EZ, DT, HT)
					 or combinations of them. Default: 0
		:param accuracy: accuracy (0 ~ 1 or 0.0 ~ 100.0, set `accuracy_percentage` accordingly). Default: 100
		:param accuracy_percentage: if True, `accuracy` goes from 0 to 1, otherwise from 0 to 100. Default: True
		"""
		self._play_data = None

		# private because these shouldn't be edited after object instantiation
		self._beatmap_path = beatmap_path
		self._score = score
		self._mods = mods
		self._accuracy = accuracy / 100 if accuracy_percentage else accuracy

	def _set_play_data(self):
		if self._play_data is None:
			self._play_data = _lua__set_play_data(self._beatmap_path, self._score, self._mods, self._accuracy)

	def calculate_pp(self):
		"""
		Calculates and returns pp

		:return: (total_pp, strain_pp, acc_pp)
		"""
		self._set_play_data()
		return _lua__get_performance_points(self._play_data)

	def calculate_stars(self):
		"""
		Calculates and returns star rating

		:return: stars
		"""
		self._set_play_data()
		return _lua__get_star_rate(self._play_data)

	# LETS naming conventions that call PEP8-like methods
	def calculatePP(self):
		"""
		See `self.calculate_pp()`
		"""
		return self.calculate_pp()

	def calculateStars(self):
		"""
		See `self.calculate_stars()`
		"""
		return self.calculate_stars()