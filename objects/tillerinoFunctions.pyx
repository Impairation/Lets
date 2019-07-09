import time
import calendar
from objects.sqlUtils import pandasQuery, wrapArrayForSelect, connectToDB

from objects import glob
import pandas as pd
import numpy as np

def player2map_performance(combo,maxCombo,misses,acc):

    A = 2
    B = 1
    C = 0.5

    if np.isnan(maxCombo) or maxCombo == 0:
        maxCombo = combo * (misses + 1)

    combo_mercy_multiplier = 1
    if misses < 10:
        combo_mercy_multiplier += A*np.exp(-B*misses)

    psycological_combo = combo_mercy_multiplier * combo;
    if (psycological_combo > maxCombo):
        psycological_combo = maxCombo

    f = C * (psycological_combo * 1.0 / maxCombo) + (1 - C) * acc/100.0;
    return f

def computeTillerinoList(userid,maps_info,dist_matrix):

    K = 10

    friends = np.argsort(dist_matrix[userid - 1000,:])[0:K] + 1000
    friends_maps = pandasQuery('SELECT DISTINCT beatmap_md5 as beatmap_md5 FROM scores WHERE userid IN {} AND time > 0 AND completed = 3'.format(wrapArrayForSelect(friends)))

    if (len(friends_maps) == 0):
        return []

    friends_maps = friends_maps['beatmap_md5']
    friends_plays = pandasQuery('SELECT * FROM scores WHERE userid IN {} AND beatmap_md5 IN {} AND completed = 3'.format(wrapArrayForSelect(friends), wrapArrayForSelect(friends_maps)))

    friends_plays = pd.merge(friends_plays,maps_info,how='left',on='beatmap_md5')
    map_scores = dict([(x,0) for x in friends_maps])
    for maphash in friends_maps:
        subset = friends_plays.loc[np.where(np.array(friends_plays['beatmap_md5'] == maphash))[0],:]
        perf = 0
        for index, row in subset.iterrows():
            perf += player2map_performance(row['max_combo_x'],row['max_combo_y'],row['misses_count'],row['accuracy']) * (1-dist_matrix[userid - 1000, int(row['userid']) - 1000])
            map_scores[maphash] += perf
    result = []
    for key, value in map_scores.items():
        result.append((key,value))
    result.sort(key=lambda x: -x[1])
    result = result[0:1500]
    return [x[0] for x in result]

def prepareTillerinoList(userid,maps_info,dist_matrix):

    glob.db = connectToDB(1)

    l = computeTillerinoList(userid,maps_info,dist_matrix)

    t = glob.db.fetch('SELECT * from tillerino_maplists WHERE user = {}'.format(str(userid)))

    if (len(l) > 0):
        if t is None:
            glob.db.execute('INSERT INTO tillerino_maplists (user,maplist) VALUES({},\' {} \')'.format(str(userid),','.join(l)))
            glob.db.execute('INSERT INTO tillerino_offsets (user,offset) VALUES({},0)'.format(str(userid)))
        else:
            glob.db.execute('UPDATE tillerino_maplists SET maplist = \' {} \' WHERE user = {}'.format(','.join(l),str(userid)))
            glob.db.execute('UPDATE tillerino_offsets SET offset = 0 WHERE user = {}'.format(str(userid)))

def prepareTillerinoAll():

    N = 1000

    glob.db = connectToDB(1)
    users = np.array(pandasQuery('SELECT user from leaderboard_std WHERE v > {}'.format(N))['user'])
    maps_info = pandasQuery('SELECT beatmap_md5,max_combo FROM beatmaps')
    dist_matrix = np.load('player_matrix.npa.npy')
    for user in users:
       prepareTillerinoList(user,maps_info, dist_matrix)

def player2player_distance(player1plays,player2plays, maps_info):

    D = 0.5

    p12 = pd.merge(player1plays,player2plays,how='inner',on=['beatmap_md5','mods'])
    if min(len(player1plays),len(player2plays)) == 0:
        return 9999
    p12 = pd.merge(p12,maps_info,how='left',on='beatmap_md5')

    common_plays = p12.loc[np.where(np.array(pd.notnull(p12['score_x']))*np.array(pd.notnull(p12['score_y'])))[0],:]
    set_distance = 1 - len(common_plays) * 1.0 /min(len(player1plays),len(player2plays))
    perf_distance = 0.0
    for index, row in p12.iterrows():
        #print(row)
        perf1 = player2map_performance(row['max_combo_x'],row['max_combo'],row['misses_count_x'],row['accuracy_x'])
        perf2 = player2map_performance(row['max_combo_y'],row['max_combo'],row['misses_count_y'],row['accuracy_y'])
        perf_distance += abs(perf1 - perf2)
    if (len(p12) > 0):
        perf_distance /= len(p12)

    f = D * perf_distance + (1 - D) * set_distance
    return f

def calculatePlayersDistanceMatrix(users, maps_info, ps):

    E = 10

    max_user = int(max(users)) - 1000 + 1
    dist_mat = np.zeros((max_user,max_user))

    for i in range(len(users)):
        for j in range(i - E, i + E):
            if j > 0 and j < len(users):
                dist_mat[i,j] = -1

    k = 0
    for i in range(len(users)):
        for j in range(i + 1,len(users)):
            userid1 = users[i]
            userid2 = users[j]

            if (dist_mat[int(userid1) - 1000,int(userid2) - 1000] < 0):
                p1 = ps.loc[np.where(np.array(ps['userid'] == userid1))[0],:]
                p2 = ps.loc[np.where(np.array(ps['userid'] == userid2))[0],:]
                f = player2player_distance(p1,p2,maps_info)
                dist_mat[int(userid1) - 1000,int(userid2) - 1000] = f
                dist_mat[int(userid2) - 1000,int(userid1) - 1000] = f
                k += 1
        dist_mat[int(users[i]) - 1000,int(users[i]) - 1000] = 99999
        return dist_mat

def preparePlayersDistanceMatrix():
    glob.db = connectToDB(1)
    users = np.array(pandasQuery('SELECT user FROM leaderboard_std ORDER BY position')['user'])
    maps_info = pandasQuery('SELECT beatmap_md5,max_combo FROM beatmaps')
    ps = pandasQuery('SELECT * FROM scores where completed = 3')
    playersMatrix = calculatePlayersDistanceMatrix(users, maps_info, ps)
    np.save('player_matrix.npa',playersMatrix)