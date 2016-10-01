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
teamName = "\'MURICA!!!"
# ---------------------------------------------------------------------

# Set initial connection data
def initialResponse():
# ------------------------- CHANGE THESE VALUES -----------------------
    return {'TeamName': teamName,
            'Characters': [
                {"CharacterName": "Assassin b",
                 "ClassId": "Paladin"},
                {"CharacterName": "Heal_Bitch",
                 "ClassId": "Paladin"},
                {"CharacterName": "TANK",
                 "ClassId": "Paladin"},
            ]}
# ---------------------------------------------------------------------

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
# ------------------ You shouldn't change above but you can ---------------
       

    #Value of characters
    def get_priority( char ):
        
        if char.classId == "Archer":
            priority = 4 * (1001 - char.attributes.health)
        elif char.classId == "Assasin":
            priority = 9 * (801 - char.attributes.health)
        elif char.classId == "Druid":
            priority = 8 * (1001 - char.attributes.health)
        elif char.classId == "Enchanter":
            priority = 10 * (1001 - char.attributes.health)
        elif char.classId == "Paladin":
            priority = 7 * (1101 - char.attributes.health)
        elif char.classId == "Sorcerer":
            priority = 6 * (801 - char.attributes.health)
        elif char.classId == "Warrior":
            priority = 3 * (1201 - char.attributes.health)
        elif char.classId == "Wizard":
            priority = 5 * (1001 - char.attributes.health)
        print("Priority is " + str(priority))
        return priority
    # Choose a target
    target = None
    


    #get list of living characters
    living_characters = []
    for character in enemyteam:
        if not character.is_dead():
            living_characters.append(character) 

    if len(living_characters) > 0:
        target = living_characters[0]

    #get highest priority
    for character in living_characters:
        if get_priority(target) < get_priority(character):
            target = character
    

    # If we found a target
    if target:
        for character in myteam:

            # If I am in range, either move towards target
            if character.in_range_of(target, gameMap):

                # Am I already trying to cast something?
                if character.casting is None:
                    cast = False
                        
                    if character.classId == "Paladin":
                        
                        #print(character.can_use_ability(3))
                        #if character.can_use_ability(3):
                        if 1 == 1:
                            a = 0
                            s = False
                            for unit in myteam:
                                if unit.attributes.health < 600 and unit.attributes.health > 0:
                                    s = True
                            if s:       
                                #heal
                                to_heal = 0
                                thing = None
                                for unit in myteam:
                                    v = get_priority(unit)
                                    if v > to_heal:
                                        thing = unit
                                        
                                actions.append({
                                            "Action": "Cast",
                                            "CharacterId": character.id,
                                            "TargetId": thing.id,
                                            "AbilityId": 3
                                        })
                                cast = True
                                break

                        if character.can_use_ability(4):
                            #stun
                            to_stun = 0
                            thing = None
                            for unit in enemyteam:
                                v = get_priority(unit)
                                if v > to_stun:
                                    thing = unit

                            print("Paladin is going to stun " + to_stun.classId + "Its health is " + str(to_stun.attributes.health))
                            actions.append({
                                        "Action": "Cast",
                                        "CharacterId": character.id,
                                        # Am I buffing or debuffing? If buffing, target myself
                                        "TargetId": thing.id,
                                        "AbilityId": 14
                                    })
                            break


                ## Not Class Specific                    
                # Was I able to cast something? Either wise attack
                if 1 == 1:
                    actions.append({
                        "Action": "Attack",
                        "CharacterId": character.id,
                        "TargetId": target.id,
                    })

            else: # Not in range, move towards
                    actions.append({
                    "Action": "Move",
                    "CharacterId": character.id,
                    "TargetId": target.id,
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
