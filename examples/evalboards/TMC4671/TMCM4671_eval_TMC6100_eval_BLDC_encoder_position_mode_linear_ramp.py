import time
import dataclasses
from pytrinamic.connections import ConnectionManager
from pytrinamic.evalboards import TMC4671_eval, TMC6100_eval
from pytrinamic.ic import TMC4671, TMC6100
import matplotlib.pyplot as plt


with ConnectionManager().connect() as my_interface:

    # Create TMC4671-EVAL and TMC6100-EVAL class which communicate over the Landungsbrücke via TMCL
    mc_eval = TMC4671_eval(my_interface)
    drv_eval = TMC6100_eval(my_interface)
    motor = mc_eval.motors[0]

    # Configure TMC6100 pwm for use with TMC4671 (disable singleline)
    drv_eval.write_register_field(TMC6100.FIELD.SINGLELINE, 0)

    # Configure TMC4671 for a BLDC motor with ABN-Encoder

    # Motor type & PWM configuration
    mc_eval.write_register_field(TMC4671.FIELD.MOTOR_TYPE, TMC4671.ENUM.MOTOR_TYPE_BLDC)
    mc_eval.write_register_field(TMC4671.FIELD.N_POLE_PAIRS, 4)
    mc_eval.write_register(TMC4671.REG.PWM_POLARITIES, 0x00000000)
    mc_eval.write_register(TMC4671.REG.PWM_MAXCNT, int(0x00000F9F))
    mc_eval.write_register(TMC4671.REG.PWM_BBM_H_BBM_L, 0x00000019)
    mc_eval.write_register_field(TMC4671.FIELD.PWM_CHOP, TMC4671.ENUM.PWM_CENTERED_FOR_FOC)
    mc_eval.write_register_field(TMC4671.FIELD.PWM_SV, 1)

    # ADC configuration
    mc_eval.write_register(TMC4671.REG.ADC_I_SELECT, 0x24000100)
    mc_eval.write_register(TMC4671.REG.dsADC_MCFG_B_MCFG_A, 0x00100010)
    mc_eval.write_register(TMC4671.REG.dsADC_MCLK_A, 0x20000000)
    mc_eval.write_register(TMC4671.REG.dsADC_MCLK_B, 0x00000000)
    mc_eval.write_register(TMC4671.REG.dsADC_MDEC_B_MDEC_A, int(0x014E014E))
    mc_eval.write_register(TMC4671.REG.ADC_I0_SCALE_OFFSET, 0xFF00835D)
    mc_eval.write_register(TMC4671.REG.ADC_I1_SCALE_OFFSET, 0xFF0083B5)

    # ABN encoder settings
    mc_eval.write_register(TMC4671.REG.ABN_DECODER_MODE, 0x00000000)
    mc_eval.write_register(TMC4671.REG.ABN_DECODER_PPR, 4096)
    mc_eval.write_register(TMC4671.REG.ABN_DECODER_PHI_E_PHI_M_OFFSET, 0)

    # Limits
    mc_eval.write_register(TMC4671.REG.PID_TORQUE_FLUX_LIMITS, 1000)

    # PI settings for Torque/Flux regulator
    mc_eval.write_register(TMC4671.REG.PID_TORQUE_P_TORQUE_I, 1279 << 16 | 193 << 0)
    mc_eval.write_register(TMC4671.REG.PID_FLUX_P_FLUX_I, 1279 << 16 | 193 << 0)

    # Init encoder (mode 0)
    print("Initializing Encoder...")
    mc_eval.write_register(TMC4671.REG.MODE_RAMP_MODE_MOTION, 0x00000008)
    mc_eval.write_register(TMC4671.REG.ABN_DECODER_PHI_E_PHI_M_OFFSET, 0x00000000)
    mc_eval.write_register(TMC4671.REG.PHI_E_SELECTION, TMC4671.ENUM.PHI_E_EXTERNAL)
    mc_eval.write_register(TMC4671.REG.PHI_E_EXT, 0x00000000)
    mc_eval.write_register(TMC4671.REG.UQ_UD_EXT, 1150)
    time.sleep(1)
    # Clear abn_decoder_count
    mc_eval.write_register(TMC4671.REG.ABN_DECODER_COUNT, 0)
    print("...done")

    # Commutation Feedback selection
    mc_eval.write_register(TMC4671.REG.PHI_E_SELECTION, TMC4671.ENUM.PHI_E_ABN)

    # ===== ABN encoder test drive =====
    @dataclasses.dataclass
    class Sample:
        timestamp: float
        position: int
    # Limits
    mc_eval.write_register(TMC4671.REG.PID_TORQUE_FLUX_LIMITS, 8000)

    # PI settings for velocity and position regulator
    mc_eval.write_register(TMC4671.REG.PID_VELOCITY_P_VELOCITY_I, 6219 << 16 | 2047 << 0)
    mc_eval.write_register(TMC4671.REG.PID_POSITION_P_POSITION_I, 8 << 16 | 0 << 0)

    # Velocity Feedback selection
    mc_eval.write_register(TMC4671.REG.VELOCITY_SELECTION, TMC4671.ENUM.VELOCITY_PHI_M_ABN)
    # Position Feedback selection
    mc_eval.write_register(TMC4671.REG.POSITION_SELECTION, TMC4671.ENUM.VELOCITY_PHI_M_ABN)

    # Switch to velocity mode
    mc_eval.write_register(TMC4671.REG.MODE_RAMP_MODE_MOTION, TMC4671.ENUM.MOTION_MODE_POSITION)

    # motion settings
    motor.linear_ramp.max_velocity = 2000
    motor.linear_ramp.max_acceleration = 1000
    motor.linear_ramp.enabled = 1
    print(motor.linear_ramp)

    samples = []

    motor.set_actual_position(0)
    time.sleep(1)

    # Rotate right
    print("Rotate right!")
    targetPos = 409600
    motor.set_axis_parameter(motor.AP.TargetPosition, targetPos)
    start_time = time.time()
    while time.time() - start_time < 5:
        samples.append(Sample(time.perf_counter(), motor.get_axis_parameter(motor.AP.ActualPosition, True)))

    # Stop
    print("Stop!")
    targetPos = 0
    motor.set_axis_parameter(motor.AP.TargetPosition, targetPos)
    start_time = time.time()
    while time.time() - start_time < 3:
        samples.append(Sample(time.perf_counter(), motor.get_axis_parameter(motor.AP.ActualPosition, True)))

    fig, ax = plt.subplots()
    t = [s.timestamp - samples[0].timestamp for s in samples]
    pos = [s.position for s in samples]
    ax.plot(t, pos, label='Position')
    ax.legend()
    plt.show()

    # Switch to stop mode
    mc_eval.write_register(TMC4671.REG.MODE_RAMP_MODE_MOTION, TMC4671.ENUM.MOTION_MODE_STOPPED)
