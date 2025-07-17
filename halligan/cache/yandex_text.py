def stage2(frames):
    # Frame 1: Distorted text image
    frame1 = frames[1]
    element1 = frame1.get_element(position='center', details='distorted text')
    element1.set_element_as(interactable='DRAGGABLE')

    # Frame 3: Input field
    frame3 = frames[3]
    element3 = frame3.get_element(position='center', details='input field')
    element3.set_element_as(interactable='INPUTTABLE')

    # Frame 2: Submit button
    frame2 = frames[2]
    element2 = frame2.get_element(position='center', details='blue button')
    element2.set_element_as(interactable='NEXT')