from halligan.utils.vision_tools import ask
from halligan.utils.action_tools import click


def stage3(frames):
    # Frame 0 provides the order of icons to click
    order_image = frames[0].image
    order = ask([order_image], "Describe the icons from the left to right", answer_type="str")

    # Frame 1 contains the clickable icons
    icons = [
        frames[1].get_interactable(0), 
        frames[1].get_interactable(1),
        frames[1].get_interactable(2),
    ]

    prompt = f"Assign each icon with the best description:\n{"\n".join([f"({i}) {desc}" for i, desc in enumerate(order)])}\n Each icon must have a unique number, all numbers must be used.\n"

    click_order = ask(
        [icon.image for icon in icons], 
        prompt, 
        answer_type="int"
    )

    # Click the icons in the specified order
    for i in click_order:
        click(icons[i])

    # Frame 2 contains the 'OK' button
    ok_button = frames[2].get_interactable(0)
    click(ok_button)