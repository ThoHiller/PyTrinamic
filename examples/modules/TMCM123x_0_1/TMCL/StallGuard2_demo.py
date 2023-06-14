"""
Sets the StallGuard2 threshold such that the stall guard value (i.e SG value) is zero
when the motor comes close to stall and also sets the stop on stall velocity to a value
one less than the actual velocity of the motor
"""
import pytrinamic
from pytrinamic.connections import ConnectionManager
from pytrinamic.modules import TMCM123x_0_1
import time

def stallguard2_init(motor, init_velocity):
    # Resetting SG2 threshold and stop on stall velocity to zero
    motor.stallguard2.set_threshold(0)
    motor.stallguard2.stop_velocity = 0
    print("Initial StallGuard2 values:")
    print(motor.stallguard2)
    print("Rotating...")
    motor.rotate(init_velocity)
    sgthresh = 0
    sgt = 0
    load_samples = []
    while (sgt == 0) and (sgthresh < 64):
        load_samples = []
        motor.stallguard2.set_threshold(sgthresh)
        time.sleep(0.2)
        sgthresh += 1
        for i in range(50):
            load_samples.append(motor.stallguard2.get_load_value())
        if not any(load_samples):
            sgt = 0
        else:
            sgt = max(load_samples)
    while 1:
        load_samples = []
        for i in range(50):
            load_samples.append(motor.stallguard2.get_load_value())
        if 0 in load_samples:
            motor.drive_settings.max_current = motor.drive_settings.max_current - 1
        else:
            break

    motor.stallguard2.stop_velocity = motor.get_actual_velocity() - 1
    print("Configured StallGuard2 parameters:")
    print(motor.stallguard2)

def main():
    pytrinamic.show_info()

    # This example is using PCAN, if you want to use another connection please change the next line.
    connection_manager = ConnectionManager("--interface kvaser_tmcl")
    with connection_manager.connect() as my_interface:
        module = TMCM123x_0_1(my_interface)
        motor = module.motors[0]

        print("Preparing parameters")
        # preparing drive settings
        motor.drive_settings.max_current = 20
        motor.drive_settings.standby_current = 8
        motor.drive_settings.boost_current = 0
        motor.drive_settings.microstep_resolution = motor.ENUM.microstep_resolution_256_microsteps
        print(motor.drive_settings)
        print(motor.linear_ramp)

        time.sleep(1.0)

        # clear position counter
        motor.actual_position = 0

        # set up StallGuard2
        print("Configuring StallGuard2 parameters...")
        stallguard2_init(motor, init_velocity = 10000)
        print("Apply load and try to stall the motor...")
        while not (motor.actual_velocity == 0):
            pass
        print("Motor stopped by StallGuard2!")

if __name__ == "__main__":
        main()