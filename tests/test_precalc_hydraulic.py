from dhnx.optimization.precalc_hydraulic import calc_v, calc_power, calc_mass_flow, \
    calc_mass_flow_P, calc_v_mf, calc_pipe_loss


def test_calc_v():
    v = calc_v(720, 0.5)
    assert round(v, 5) == 1.01859


def test_calc_power():
    P_th = calc_power(80, 50, 3)
    assert round(P_th, 5) == 393070.3261


def test_calc_mass_flow():
    mf = calc_mass_flow(3, 0.5, 20)
    assert round(mf, 5) == 587.99192


def test_calc_mass_flow_P():
    mf = calc_mass_flow_P(50000, 20, 5)
    assert round(mf, 5) == 2.3896


def test_calc_v_mf():
    v = calc_v_mf(200, 0.5, 20)
    assert round(v, 5) == 1.02042


def test_calc_pipe_loss():
    loss = calc_pipe_loss(20, 0.1, 10)
    assert round(loss, 5) == 1
