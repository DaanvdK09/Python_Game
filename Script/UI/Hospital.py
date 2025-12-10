#What to do when the player enters a hospital
def enter_hospital(player, hospital_npc):
    hospital_npc.speak("Welcome to the Pokémon Center! Your Pokémon will be fully healed here.")
    if player.has_pokemon():
        hospital_npc.speak("Let me take care of your team right away.")
        player.heal_all_pokemon()
        hospital_npc.speak("All done! Your Pokémon are healthy and ready to go.")
    else:
        hospital_npc.speak("It seems you don't have any Pokémon with you. Come back when you do!")
    hospital_npc.speak("Take care on your journey!")

