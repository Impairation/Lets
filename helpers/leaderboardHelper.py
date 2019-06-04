from common.log import logUtils as log
from common.ripple import scoreUtils
from objects import glob
from common.ripple import userUtils

def rxgetRankInfo(userID, gameMode):
	"""
	Get userID's current rank, user above us and pp/score difference

	:param userID: user
	:param gameMode: gameMode number
	:return: {"nextUsername": "", "difference": 0, "currentRank": 0}
	"""
	data = {"nextUsername": "", "difference": 0, "currentRank": 0}
	k = "ripple:relaxboard:{}".format(scoreUtils.readableGameMode(gameMode))
	position = userUtils.rxgetGameRank(userID, gameMode) - 1
	log.debug("Our position is {}".format(position))
	if position is not None and position > 0:
		aboveUs = glob.redis.zrevrange(k, position - 1, position)
		log.debug("{} is above us".format(aboveUs))
		if aboveUs is not None and len(aboveUs) > 0 and aboveUs[0].isdigit():
			# Get our rank, next rank username and pp/score difference
			myScore = glob.redis.zscore(k, userID)
			otherScore = glob.redis.zscore(k, aboveUs[0])
			nextUsername = userUtils.getUsername(aboveUs[0])
			if nextUsername is not None and myScore is not None and otherScore is not None:
				data["nextUsername"] = nextUsername
				data["difference"] = int(myScore) - int(otherScore)
	else:
		position = 0

	data["currentRank"] = position + 1
	return data

def getRankInfo(userID, gameMode):
	"""
	Get userID's current rank, user above us and pp/score difference

	:param userID: user
	:param gameMode: gameMode number
	:return: {"nextUsername": "", "difference": 0, "currentRank": 0}
	"""
	data = {"nextUsername": "", "difference": 0, "currentRank": 0}
	k = "ripple:leaderboard:{}".format(scoreUtils.readableGameMode(gameMode))
	position = userUtils.getGameRank(userID, gameMode) - 1
	log.debug("Our position is {}".format(position))
	if position is not None and position > 0:
		aboveUs = glob.redis.zrevrange(k, position - 1, position)
		log.debug("{} is above us".format(aboveUs))
		if aboveUs is not None and len(aboveUs) > 0 and aboveUs[0].isdigit():
			# Get our rank, next rank username and pp/score difference
			myScore = glob.redis.zscore(k, userID)
			otherScore = glob.redis.zscore(k, aboveUs[0])
			nextUsername = userUtils.getUsername(aboveUs[0])
			if nextUsername is not None and myScore is not None and otherScore is not None:
				data["nextUsername"] = nextUsername
				data["difference"] = int(myScore) - int(otherScore)
	else:
		position = 0

	data["currentRank"] = position + 1
	return data

def rxupdate(userID, newScore, gameMode):
	"""
	Update gamemode's leaderboard.
	Doesn't do anything if userID is banned/restricted.

	:param userID: user
	:param newScore: new score or pp
	:param gameMode: gameMode number
	"""
	mode = scoreUtils.readableGameMode(gameMode)

	newPlayer = False
	us = glob.db.fetch("SELECT * FROM relaxboard_{} WHERE user=%s LIMIT 1".format(mode), [userID])
	if us is None:
		newPlayer = True

	# Find player who is right below our score
	target = glob.db.fetch("SELECT * FROM relaxboard_{} WHERE v <= %s ORDER BY position ASC LIMIT 1".format(mode), [newScore])
	plus = 0
	if target is None:
		# Wow, this user completely sucks at this game.
		target = glob.db.fetch("SELECT * FROM relaxboard_{} ORDER BY position DESC LIMIT 1".format(mode))
		plus = 1

	# Set newT
	if target is None:
		# Okay, nevermind. It's not this user to suck. It's just that no-one has ever entered the leaderboard thus far.
		# So, the player is now #1. Yay!
		newT = 1
	else:
		# Otherwise, just give them the position of the target.
		newT = target["position"] + plus

	# Make some place for the new "place holder".
	if newPlayer:
		glob.db.execute("UPDATE relaxboard_{} SET position = position + 1 WHERE position >= %s ORDER BY position DESC".format(mode), [newT])
	else:
		glob.db.execute("DELETE FROM relaxboard_{} WHERE user = %s".format(mode), [userID])
		glob.db.execute("UPDATE relaxboard_{} SET position = position + 1 WHERE position < %s AND position >= %s ORDER BY position DESC".format(mode), [us["position"], newT])

	#if newT <= 1:
	#	log.info("{} is now #{} ({})".format(userID, newT, mode), "bunker")

	# Finally, insert the user back.
	glob.db.execute("INSERT INTO relaxboard_{} (position, user, v) VALUES (%s, %s, %s);".format(mode), [newT, userID, newScore])
	if gameMode == 0:
		newPlayer = False
		us = glob.db.fetch("SELECT * FROM users_relax_peak_rank WHERE userid = %s LIMIT 1", [userID])
		if us is None:
			newPlayer = True
		if newPlayer:
			glob.db.execute("INSERT INTO users_relax_peak_rank (userid, peak_rank) VALUES (%s, %s);", [userID, newT])
		else:
			if us["peak_rank"] > newT:
						glob.db.execute("UPDATE users_relax_peak_rank SET peak_rank = %s WHERE userid = %s", [newT,userID])
						
	
	if userUtils.isAllowed(userID):
		log.debug("Updating relaxboard...")
		glob.redis.zadd("ripple:relaxboard:{}".format(scoreUtils.readableGameMode(gameMode)), str(userID), str(newScore))
	else:
		log.debug("Relaxboard update for user {} skipped (not allowed)".format(userID))
	
def update(userID, newScore, gameMode):
	"""
	Update gamemode's leaderboard.
	Doesn't do anything if userID is banned/restricted.

	:param userID: user
	:param newScore: new score or pp
	:param gameMode: gameMode number
	"""
	mode = scoreUtils.readableGameMode(gameMode)

	newPlayer = False
	us = glob.db.fetch("SELECT * FROM leaderboard_{} WHERE user=%s LIMIT 1".format(mode), [userID])
	if us is None:
		newPlayer = True

	# Find player who is right below our score
	target = glob.db.fetch("SELECT * FROM leaderboard_{} WHERE v <= %s ORDER BY position ASC LIMIT 1".format(mode), [newScore])
	plus = 0
	if target is None:
		# Wow, this user completely sucks at this game.
		target = glob.db.fetch("SELECT * FROM leaderboard_{} ORDER BY position DESC LIMIT 1".format(mode))
		plus = 1

	# Set newT
	if target is None:
		# Okay, nevermind. It's not this user to suck. It's just that no-one has ever entered the leaderboard thus far.
		# So, the player is now #1. Yay!
		newT = 1
	else:
		# Otherwise, just give them the position of the target.
		newT = target["position"] + plus

	# Make some place for the new "place holder".
	if newPlayer:
		glob.db.execute("UPDATE leaderboard_{} SET position = position + 1 WHERE position >= %s ORDER BY position DESC".format(mode), [newT])
	else:
		glob.db.execute("DELETE FROM leaderboard_{} WHERE user = %s".format(mode), [userID])
		glob.db.execute("UPDATE leaderboard_{} SET position = position + 1 WHERE position < %s AND position >= %s ORDER BY position DESC".format(mode), [us["position"], newT])

	#if newT <= 1:
	#	log.info("{} is now #{} ({})".format(userID, newT, mode), "bunker")

	# Finally, insert the user back.
	glob.db.execute("INSERT INTO leaderboard_{} (position, user, v) VALUES (%s, %s, %s);".format(mode), [newT, userID, newScore])
	if gameMode == 0:
		newPlayer = False
		us = glob.db.fetch("SELECT * FROM users_peak_rank WHERE userid = %s LIMIT 1", [userID])
		if us is None:
			newPlayer = True
		if newPlayer:
			glob.db.execute("INSERT INTO users_peak_rank (userid, peak_rank) VALUES (%s, %s);", [userID, newT])
		else:
			if us["peak_rank"] > newT:
						glob.db.execute("UPDATE users_peak_rank SET peak_rank = %s WHERE userid = %s", [newT,userID])
					
					
	if userUtils.isAllowed(userID):
		log.debug("Updating leaderboard...")
		glob.redis.zadd("ripple:leaderboard:{}".format(scoreUtils.readableGameMode(gameMode)), str(userID), str(newScore))
	else:
		log.debug("Leaderboard update for user {} skipped (not allowed)".format(userID))

def rxupdateCountry(userID, newScore, gameMode):
	"""
	Update gamemode's country leaderboard.
	Doesn't do anything if userID is banned/restricted.

	:param userID: user, country is determined by the user
	:param newScore: new score or pp
	:param gameMode: gameMode number
	:return:
	"""
	if userUtils.isAllowed(userID):
		country = userUtils.getCountry(userID)
		if country is not None and len(country) > 0 and country.lower() != "xx":
			log.debug("Updating {} country relaxboard...".format(country))
			k = "ripple:relaxboard:{}:{}".format(scoreUtils.readableGameMode(gameMode), country.lower())
			glob.redis.zadd(k, str(userID), str(newScore))
	else:
		log.debug("Country relaxboard update for user {} skipped (not allowed)".format(userID))

		
def updateCountry(userID, newScore, gameMode):
	"""
	Update gamemode's country leaderboard.
	Doesn't do anything if userID is banned/restricted.

	:param userID: user, country is determined by the user
	:param newScore: new score or pp
	:param gameMode: gameMode number
	:return:
	"""
	if userUtils.isAllowed(userID):
		country = userUtils.getCountry(userID)
		if country is not None and len(country) > 0 and country.lower() != "xx":
			log.debug("Updating {} country leaderboard...".format(country))
			k = "ripple:leaderboard:{}:{}".format(scoreUtils.readableGameMode(gameMode), country.lower())
			glob.redis.zadd(k, str(userID), str(newScore))
	else:
		log.debug("Country leaderboard update for user {} skipped (not allowed)".format(userID))
