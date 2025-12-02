"""
Introduction dialogue builder for the professor NPC.

This module improves the default starter dialogue by:
 - using a friendly, helpful tone for the professor
 - mentioning controls and gameplay hooks with short examples
 - offering a quick optional tutorial if the UI supports choice prompts
 - falling back gracefully for simpler `professor.speak(line)` usage
"""

def introduction_dialogue(player, professor):
    """Runs a friendly introductory conversation with the professor NPC.

    player: Character-like object (may contain attributes like .name)
    professor: NPC-like object with a `speak(text)` method and optionally an
               `ask(prompt, options)` or `prompt_choice(prompt, options)` method
    """

    # Resolve a display name: try `name` then fallback to 'Trainer'
    player_name = getattr(player, "name", None) or getattr(player, "display_name", None) or "Trainer"

    # A short, friendly opening that sets the tone and story hook
    opening = [
        f"Ah! There you are, {player_name}. Welcome!",
        "I am the professor here in this city. I study the bond between trainers and pokémon.",
        "Your journey is about exploration, friendship, and learning how to master the challenges ahead.",
    ]

    # Quick gameplay hints; keep them short and action-focused
    mechanics = [
        "Move around using the arrow keys or WASD to explore.",
        "Press 'E' to interact with people and objects.",
        "Open your inventory with 'I' and the map with 'M' to keep track of things.",
        "Watch your pokémon's health and status; bring them to the Pokémon Center if they get hurt.",
    ]

    # Wrap up with a story prompt and an offer to run a tutorial
    closing = [
        "If you'd like, I can take you through a quick tutorial to get you started.",
        "Otherwise, feel free to explore; your first goal is to head to the route just outside the town.",
        "Ready to begin?"
    ]

    # Speak all opening lines
    for line in opening:
        professor.speak(line)

    # Explain the core mechanics
    for line in mechanics:
        professor.speak(line)

    # Closing lines and optional tutorial prompt
    for line in closing:
        professor.speak(line)

    # If the professor (or UI) supports a prompt with choices, ask the player whether they
    # want a brief hands-on tutorial. We try a few common method names to remain compatible.
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
            # Many menu functions return a string or index; we accept either form.
            res = choice_fn("Would you like a quick tutorial?", ["Yes, please", "No, thanks"])
            if isinstance(res, int):
                tutorial_selected = (res == 0)
            elif isinstance(res, str):
                tutorial_selected = (res.lower().startswith("y") or res.lower() == "yes" or res.lower() == "yes, please")
            else:
                # Duck-typed: truthiness of the response indicates 'yes'
                tutorial_selected = bool(res)
        except Exception:
            # If the prompt fails for any reason, fall back to showing tutorial lines
            tutorial_selected = True

    # If the UI doesn't support choices, default to a short inline tutorial to guide the player
    if tutorial_selected or choice_fn is None:
        run_tutorial(player, professor)

    # Final send-off
    professor.speak("That's it from me—good luck, and return any time you need advice!")


def run_tutorial(player, professor):
    """Deliver a short, hands-on tutorial using `professor.speak()` calls.

    This is intentionally short, but gives clear steps the player can follow.
    """
    steps = [
        "First: let's practice moving. Try walking to the door in front of you.",
        "Great! Now interact (press 'E') with the signpost to read more information.",
        "Tip: Press 'I' to open your inventory. Try opening and closing it now.",
        "If you see tall grass, step into it — wild Pokémon may appear there for you to catch.",
        "You can manage team order and items from the menu. Don't forget to save!",
    ]

    professor.speak("Let's try a few simple tasks — I'll be here to watch and help.")
    for s in steps:
        professor.speak(s)

    professor.speak("Nice work! Head outside whenever you're ready to begin your journey.")
        
