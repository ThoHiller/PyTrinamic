import time
import pytrinamic
from pytrinamic.connections import ConnectionManager
from pytrinamic.evalboards import TMC2208_eval

pytrinamic.show_info()

with ConnectionManager().connect() as my_interface:
    print(my_interface)

    # Create TMC2209-EVAL class which communicates over the Landungsbrücke via TMCL
    eval_board = TMC2208_eval(my_interface)
    motor = eval_board.motors[0]

    print("Rotating...")
    motor.rotate(1*4000)
    time.sleep(2)

    print("Stopping...")
    motor.stop()
    time.sleep(1)

    print("Moving back to 0")
    motor.move_to(0, 2000)

    # Wait until position 0 is reached
    while motor.actual_position != 0:
        print("Actual position: " + str(motor.actual_position))
        time.sleep(0.2)

    print("Reached position 0")

print("\nReady.")
