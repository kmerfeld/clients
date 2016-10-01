#!/usr/bin/python2
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
teamName = "refactor"
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
                {"CharacterName": "Archer3",
                 "ClassId": "Archer"},
            ]}
# ---------------------------------------------------------------------
class Bot():
    def __init__(self):
        self.myattack = [0, 0, 0]
        self.mydefense = [0, 0, 0]
        self.enemyattack = [0, 0, 0]
        self.enemydefense = [0, 0, 0]

        self.damageWeight = 1.0
        self.healthWeight = .1 #must be floating point
        self.armorWeight = .1
        self.useArmorDebuff = False

        self.kiteReleased = False

        self.init = True
        self.startingPosition = 0

        self.turnCount = 0

        self.previousHealth = [0,0,0]

    def moveToTarget(self, character, target):
        self.actions.append({
            "Action": "Move",
            "CharacterId": character.id,
            "TargetId": target.id,
        })

    def moveToLocation(self, character, location):
        self.actions.append({
            "Action": "Move",
            "CharacterId": character.id,
            "Location": location,
        })

    def cast(self, character, abilityId):
        self.actions.append({
        "Action": "Cast",
        "CharacterId": character.id,
        "TargetId": character.id,
        "AbilityId": int(abilityId)
        })

    def attack(self, character, target):
        self.actions.append({
            "Action": "Attack",
            "CharacterId": character.id,
            "TargetId": target.id,
        })

    def get_enemy_target(self, myteam):
        #assume target is the one with the lowest health
        #TODO: make this not terrible

        lowest_health = 9999
        lowest_char = None
        for unit in self.myteam:
            print(str(unit.attributes.health))
            if not unit.is_dead():
                if unit.attributes.health < lowest_health:
                    lowest_health = unit.attributes.health
                    lowest_char = unit;

        #dead_count is to make sure it doesnt crash if everyone is dead
        dead_count = 0
        for unit in self.myteam:
            if unit.is_dead():
                dead_count += 1
                print("dead count is " + str(dead_count))

        if dead_count == 3:
            return self.myteam[0]
        else:
            return lowest_char

    def archer(self, character):
        if character.attributes.health < 0.5*character.attributes.maxHealth and character.position != self.startingPosition and not kiteReleased:
            self.kiteReleased = True
            self.moveToLocation(character, self.startingPosition)

        elif character.in_range_of(self.target, gameMap):
            self.burst = 0
            sprint = 12
            armorDebuff = 2
            # Am I already trying to cast something?
            if character.casting is None:
                cast = False
                if character.attributes.get_attribute("Stunned") or character.attributes.get_attribute("Silenced") or character.attributes.get_attribute("Rooted"): #burst if crowd controlled
                    crowdcontrolled = True
                    self.cast(character, self.burst)
                    cast = True

                else:
                    for abilityId, cooldown in character.abilities.items():
                        # Do I have an ability not on cooldown
                        if self.useArmorDebuff and abilityId == armorDebuff and cooldown == 0: #cast armor debuff
                            # If I can, then cast it
                            ability = game_consts.abilitiesList[int(abilityId)]
                            # Get ability
                            self.cast(character, abilityId)
                            cast = True
                            break
                # Was I able to cast something? Either wise attack
                if not cast:
                    self.attack(character, self.target)
        else: # Not in range, move towards
            self.moveToTarget(character, self.target)

# Determine actions to take on a given turn, given the server response
    def processTurn(self, serverResponse):
    # --------------------------- CHANGE THIS SECTION -------------------------
        # Setup helper variables
        self.actions = []
        self.myteam = []
        self.enemyteam = []
        # Find each team and serialize the objects
        for team in serverResponse["Teams"]:
            if team["Id"] == serverResponse["PlayerInfo"]["TeamId"]:
                for characterJson in team["Characters"]:
                    character = Character()
                    character.serialize(characterJson)
                    self.myteam.append(character)
            else:
                for characterJson in team["Characters"]:
                    character = Character()
                    character.serialize(characterJson)
                    self.enemyteam.append(character)


        if self.init: # run this stuff once after figuring out the enemy composition
            print("init")
            init = False
            for d in range(0,len(self.enemyteam)):
                self.enemyattack[d] = self.enemyteam[d].attributes.damage * self.damageWeight
            for d in range(0,len(self.myteam)):
                self.myattack[d] = self.myteam[d].attributes.damage * self.damageWeight
            self.startingPosition = (self.myteam[0].position[0], self.myteam[0].position[1])
    # ------------------ You shouldn't change above but you can ---------------

        deliciousness = [0,0,0] # appeal to attack
        maxDelish = 0
        maxDanger = 0

        for d in range(0,len(self.enemyteam)):
            if self.enemyteam[d].is_dead():
                self.enemyattack[d] = 0
                self.enemydefense[d] = sys.maxint
            else:
                self.enemydefense[d] = self.enemyteam[d].attributes.health * self.healthWeight + self.enemyteam[d].attributes.armor * self.armorWeight
                deliciousness[d] = self.enemyattack[d] / self.enemydefense[d]
                if deliciousness[d] > deliciousness[maxDelish]:
                    maxDelish = d

                                                                                                                                                       

        # Choose a target
        self.target = self.enemyteam[maxDelish]
        print(str(self.get_enemy_target(self.myteam).name))
        
    #-------------------Archer----------------------------------------

        character = self.myteam[0]
        self.archer(character)

    #------------------------------------------------------
        character = self.myteam[1]
        self.archer(character)

    #-------------------------------------------------------

        character = self.myteam[2]
        self.archer(character)

    #-------------------------------------------------------
        # Send actions to the server
        return {
            'TeamName': teamName,
            'Actions': self.actions
        }
# ---------------------------------------------------------------------

bot = Bot()
def processTurn(serverResponse):
    return bot.processTurn(serverResponse)

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
