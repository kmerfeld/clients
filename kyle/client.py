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
                 "ClassId": "Assassin"},
                {"CharacterName": "Heal_Bitch",
                 "ClassId": "Druid"},
                {"CharacterName": "TANK",
                 "ClassId": "Assassin"},
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
            priority = 7
        if char.classId == "Assasin":
            priority = 9
        if char.classId == "Druid":
            priority = 8
        if char.classId == "Enchanter":
            priority = 10
        if char.classId == "Paladin":
            priority = 6
        if char.classId == "Sorcerer":
            priority = 5
        if char.classId == "Warrior":
            priority = 4
        if char.classId == "Wizard":
            priority = 3

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
            #if character.in_range_of(enemyteam[0], gameMap):
            #    print("In range Still moving!!!!" + enemyteam[0].name)
            #if character.in_range_of(enemyteam[1], gameMap):
            #    print("In range Still moving!!!!" + enemyteam[1].name)
            #if character.in_range_of(enemyteam[2], gameMap):
            #    print("In range Still moving!!!!" + enemyteam[2].name)

            # If I am in range, either move towards target
            if character.in_range_of(target, gameMap):
                #TODO: reconsider target

                # Am I already trying to cast something?
                if character.casting is None:
                    cast = False

                    for abilityId, cooldown in character.abilities.items():
                        #TODO: set move order for each class

                        
                        #Druid
                        if character.classId == "Druid":
                            #heal
                            char = myteam[0]
            
                            #get lowest health
                            #TODO: fix this
                            for unit in myteam:
                                if unit.attributes.health > char:
                                        char = unit
                        

                            #check if not worth healing
                            if not char.attributes.health > 700 and char.attributes.health > 0:         

                                print("Druid is going to heal " + char.classId + "Its health is " + str(char.attributes.health))
                                print(int(abilityId))
                                #apply heal
                                
                                #Do I have an ability not on cooldown
                                if cooldown == 0:
                                    # If I can, then cast it
                            

                                    ability = game_consts.abilitiesList[0]
                                    # Get ability
                                    actions.append({
                                        "Action": "Cast",
                                        "CharacterId": character.id,
                                        # Am I buffing or debuffing? If buffing, target myself
                                        "TargetId": char.id,
                                        "AbilityId": 3
                                    })
                                    cast = True
                                    break

                            

                        # Do I have an ability not on cooldown
                        if cooldown == 0:
                            # If I can, then cast it
                            ability = game_consts.abilitiesList[int(abilityId)]
                            # Get ability
                            actions.append({
                                "Action": "Cast",
                                "CharacterId": character.id,
                                # Am I buffing or debuffing? If buffing, target myself
                                "TargetId": target.id if ability["StatChanges"][0]["Change"] < 0 else character.id,
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
