from __future__ import print_function
import socket
import json
import os
import random
import sys
from socket import error as SocketError
import errno
sys.path.append("../..")
import src.game.game_constants as game_consts
from src.game.character import *
from src.game.gamemap import *
# Game map that you can use to query 
gameMap = GameMap()

# --------------------------- SET THIS IS UP -------------------------
teamName = "ming"
# ---------------------------------------------------------------------

# Set initial connection data
def initialResponse():
# ------------------------- CHANGE THESE VALUES -----------------------
    return {'TeamName': teamName,
            'Characters': [
                {"CharacterName": "Archer1",
                 "ClassId": "Archer"},
                {"CharacterName": "Archer2",
                 "ClassId": "Archer"},
                {"CharacterName": "Enchanter",
                 "ClassId": "Enchanter"},
            ]}
# ---------------------------------------------------------------------

myattack = [0, 0, 0]
mydefense = [0, 0, 0]
enemyattack = [0, 0, 0]
enemydefense = [0, 0, 0]

damageWeight = 1.0
healthWeight = .1 #must be floating point
armorWeight = .1

global init
init = True


def printDanger(dangermap):
    for a in range(0,5):
        for b in range(0,5):
            print("%.5f" % dangermap[(b,a)], end="\t")
        print("")

    print()
#    for a in dangermap:
#        print(str(a) + "\t" + str(dangermap[a]))

def pointSlope(p1, p2):
    return (p2[1]-p1[1])/(p2[0]-p1[0])

def adjacentTiles(p, attackRange):
    t = []
    px, py = p
    for a in range(-attackRange, attackRange):
        tx = px + a
        if tx < 0 or tx > 4:
            continue
        for b in range(-attackRange, attackRange):
            ty = py+b
            if gameMap.is_inbounds([tx,ty]):
                t.append((tx,ty))
    return t

def tilesAway(p, dist):
    t = []
    px, py = p
    for a in range(-dist, dist+1):
        tx = px + a
        if tx < 0 or tx > 4:
            continue
        for b in [-dist, dist]:
            ty = py+b
            if gameMap.is_inbounds([tx,ty]):
                t.append((tx,ty))
    for a in [-dist, dist]:
        tx = px + a
        if tx < 0 or tx > 4:
            continue
        for b in range(-dist+1, dist):
            ty = py+b
            if gameMap.is_inbounds([tx,ty]):
                t.append((tx,ty))
    return t
def distance(p1, p2):
    return ((p2[0]-p1[0])**2.0 + (p2[1]-p1[1])**2.0)**.5

# Determine actions to take on a given turn, given the server response
def processTurn(serverResponse):


# --------------------------- CHANGE THIS SECTION -------------------------
    # Setup helper variables
    actions = []
    myteam = []
    enemyteam = []
    # Find each team and serialize the objects
    for team in serverResponse["Teams"]:
        if team["Id"] == serverResponse["PlayerInfo"]["TeamId"]:
            for characterJson in team["Characters"]:
                character = Character()
                character.serialize(characterJson)
                myteam.append(character)
        else:
            for characterJson in team["Characters"]:
                character = Character()
                character.serialize(characterJson)
                enemyteam.append(character)
# ------------------ You shouldn't change above but you can ---------------or 
    global init
    if init: # run this stuff once after figuring out the enemy composition
        print("init")
        init = False
        for d in range(0,len(enemyteam)):
            enemyattack[d] = enemyteam[d].attributes.damage * damageWeight
        for d in range(0,len(myteam)):
            myattack[d] = myteam[d].attributes.damage * damageWeight


    dangermap = {
            ( 0 ,  0):0,
           ( 0 ,  1):0,
           ( 0 ,  2):0,
           ( 0 ,  3):0,
           ( 0 ,  4):0,
           ( 1 ,  0):0,
           ( 1 ,  1):0,
           ( 1 ,  2):0,
           ( 1 ,  3):0,
           ( 1 ,  4):0,
           ( 2 ,  0):0,
           ( 2 ,  1):0,
           ( 2 ,  2):0,
           ( 2 ,  3):0,
           ( 2 ,  4):0,
           ( 3 ,  0):0,
           ( 3 ,  1):0,
           ( 3 ,  2):0,
           ( 3 ,  3):0,
           ( 3 ,  4):0,
           ( 4 ,  0):0,
           ( 4 ,  1):0,
           ( 4 ,  2):0,
           ( 4 ,  3):0,
           ( 4 ,  4):0
           }
    deliciousness = [0,0,0] # appeal to attack
    maxDelish = 0
    maxDanger = 0

    for d in range(0,len(enemyteam)):
        if enemyteam[d].is_dead():
            enemyattack[d] = 0
            enemydefense[d] = sys.maxint
        else:
            tloc = tuple(enemyteam[d].position) # store the location tuple
            t = enemyattack[d] + dangermap[tloc]
            dangermap[tloc] = t
            if t > maxDanger:
                maxDanger = t
            for a in range(1, 5):
                for b in tilesAway(tloc, a):
                    if gameMap.is_inbounds(b):
                        tb = tuple(b)
                        t = dangermap[tb]+ dangermap[tloc]*(2.718**(-distance(b,tloc)*(2.1-enemyteam[d].attributes.attackRange)))
                        dangermap[tb] = t
                        if t > maxDanger:
                            maxDanger = t

            enemydefense[d] = enemyteam[d].attributes.health * healthWeight + enemyteam[d].attributes.armor * armorWeight
            deliciousness[d] = enemyattack[d] / enemydefense[d]
            if deliciousness[d] > deliciousness[maxDelish]:
                maxDelish = d

    
    for a in range(0,5):
        for b in range(0,5):
            try:
                dangermap[(b,a)] = dangermap[(b,a)]/maxDanger
            except ZeroDivisionError: # celebratory division by zero when we win
                pass

    riskiness = 0.8 
    highrisk = riskiness + .1
    lowrisk = riskiness - 0.1


    for d in range(0,len(myteam)):
        if myteam[d].is_dead():
            myattack[d] = 0
            mydefense[d] = sys.maxint
        else:
            mydefense[d] = myteam[d].attributes.health * healthWeight + myteam[d].attributes.armor * armorWeight


    print(enemyattack)
    print(enemydefense)
    print(deliciousness)


#    for c in myteam:
#        print(c.classId + "\t" + str(c.buffs) + "\t" + str(c.debuffs))
#    for a in game_consts.abilitiesList[3]:
#        print(a + "\t" +str( game_consts.abilitiesList[3][a]))

    printDanger(dangermap)

    # Choose a target
    target = enemyteam[maxDelish]
    #for character in enemyteam:
    #    if not character.is_dead():
    #        target = character
    #        break

    for character in myteam:
                if target:

                        # If I am in range, either move towards target
                        if character.in_range_of(target, gameMap):# and dangermap[character.position] < highrisk:
                            # Am I already trying to cast something?
                            if character.casting is None:
                                cast = False
                                for abilityId, cooldown in character.abilities.items():
                                    # Do I have an ability not on cooldown
                                    if cooldown == 0:
                                        # If I can, then cast it
                                        ability = game_consts.abilitiesList[int(abilityId)]
                                        if character.classId == "Archer" and  ability["StatChanges"][0]["Change"] >= 0: # only use offensive abilities
                                            continue
                                        # Get ability
                                        if character.classId == "Enchanter":
                                            print(abilityId)
                                            print(myteam[0].name)
                                        actions.append({
                                            "Action": "Cast",
                                            "CharacterId": character.id,
                                            # Am I buffing or debuffing? If buffing, target myself
                                            "TargetId": target.id if ability["StatChanges"][0]["Change"] < 0 else myteam[0].id,
                                            "AbilityId": int(abilityId)
                                        })
                                        cast = True
                                        break
                                # Was I able to cast something? Either wise attack
                                if not cast:
                                    actions.append({
                                        "Action": "Attack",
                                        "CharacterId": character.id,
                                        "TargetId": target.id,
                                    })
                        else: # Not in range, move towards
                            if dangermap[character.position] < riskiness:# or not gameMap.in_vision_of(character.position, target.position):
                                actions.append({
                                    "Action": "Move",
                                    "CharacterId": character.id,
                                    "TargetId": target.id # top right
                                })


    # Send actions to the server
    return {
        'TeamName': teamName,
        'Actions': actions
    }
# ---------------------------------------------------------------------

# Main method
# @competitors DO NOT MODIFY
if __name__ == "__main__":
    # Config
    conn = ('localhost', 1337)
    if len(sys.argv) > 2:
        conn = (sys.argv[1], int(sys.argv[2]))

    # Handshake
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(conn)

    # Initial connection
    s.sendall(json.dumps(initialResponse()) + '\n')

    # Initialize test client
    game_running = True
    members = None

    # Run game
    try:
        data = s.recv(1024)
        while len(data) > 0 and game_running:
            value = None
            if "\n" in data:
                data = data.split('\n')
                if len(data) > 1 and data[1] != "":
                    data = data[1]
                    data += s.recv(1024)
                else:
                    value = json.loads(data[0])

                    # Check game status
                    if 'winner' in value:
                        game_running = False

                    # Send next turn (if appropriate)
                    else:
                        msg = processTurn(value) if "PlayerInfo" in value else initialResponse()
                        s.sendall(json.dumps(msg) + '\n')
                        data = s.recv(1024)
            else:
                data += s.recv(1024)
    except SocketError as e:
        if e.errno != errno.ECONNRESET:
            raise  # Not error we are looking for
        pass  # Handle error here.
s.close()
