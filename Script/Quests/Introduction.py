#Introduction dialogue/tutorial with professor NPC.

def introduction_dialogue(player, professor):

    player_name = getattr(player, "name", None) or getattr(player, "display_name", None) or "Trainer"

    opening = [
        f"Ah! There you are, {player_name}. Welcome!",
        "I am the professor here in this city. I study the bond between trainers and pokémon.",
        "Your journey is about exploration, friendship, and learning how to master the challenges ahead.",
    ]

    mechanics = [
        "Move around using the arrow keys or WASD to explore.",
        "Press 'E' to interact with people and objects.",
        "Open your inventory with 'B' and the map with 'M' to keep track of things.",
        "Watch your pokémon's health and status; bring them to the Pokémon Center if they get hurt.",
    ]

    closing = [
        "If you'd like, I can take you through a quick tutorial to get you started.",
        "Otherwise, feel free to explore; your first goal is to head to the route just outside the town.",
        "Ready to begin?"
    ]

    for line in opening:
        professor.speak(line)

    for line in mechanics:
        professor.speak(line)

    for line in closing:
        professor.speak(line)

    prompt_methods = [
        "ask",
        "prompt",
        "prompt_choice",
        "menu",
        "choice",
    ]

    choice_fn = None
    for name in prompt_methods:
        if hasattr(professor, name) and callable(getattr(professor, name)):
            choice_fn = getattr(professor, name)
            break

    tutorial_selected = False
    if choice_fn:
        try:
            res = choice_fn("Would you like a quick tutorial?", ["Yes, please", "No, thanks"])
            if isinstance(res, int):
                tutorial_selected = (res == 0)
            elif isinstance(res, str):
                tutorial_selected = (res.lower().startswith("y") or res.lower() == "yes" or res.lower() == "yes, please")
            else:
                tutorial_selected = bool(res)
        except Exception:
            tutorial_selected = True

    if tutorial_selected or choice_fn is None:
        run_tutorial(player, professor)

    professor.speak("That's it from me—good luck, and return any time you need advice!")

def run_tutorial(player, professor):
    steps = [
        "First: let's practice moving. Try walking to the green house next to you.",
        "Tip: Press 'TAB' to open your bag. Try opening and closing it now.",
        "If you see tall grass, step into it — wild Pokémon may appear there for you to catch.",
        "You can manage team order and items from the menu. Don't forget to save!",
    ]

    professor.speak("Let's try a few simple tasks — I'll be here to watch and help.")
    for s in steps:
        professor.speak(s)

    professor.speak("Nice work! Head outside whenever you're ready to begin your journey.")
        
