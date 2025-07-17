def stage2(frames):
    # Frame 0: Input field
    frame_0 = frames[0]
    input_element = frame_0.get_element(position='down', details='rectangular input field')
    input_element.set_element_as('INPUTTABLE')

    # Frame 1: Distorted text
    frame_1 = frames[1]
    # Frame 1 is dependent on Frame 0, so it is non-interactable