from dhnx.optimization.precalc_hydraulic import calc_v, calc_power, calc_mass_flow, \
    calc_mass_flow_P, calc_v_mf, calc_pipe_loss, calc_k_v, calc_Re, calc_lambda_laminar, calc_d_p, \
    calc_lambda_turb1, calc_lambda_turb2, calc_lambda_rough, calc_lambda_turb3, calc_lambda_transition


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


def test_calc_k_v():
    k_v = calc_k_v(5, 4)
    assert k_v == 1.25


def test_calc_Re():
    Re = calc_Re(1, 2, 4)
    assert Re == 0.5


def test_calc_lam_laminar():
    lam = calc_lambda_laminar(64)
    assert lam == 1


def test_calc_d_p():
    dp = calc_d_p(1, 1, 2, 1, 2)
    assert dp == 1


def test_calc_lam_turb1():
    lam = calc_lambda_turb1(0.001)
    assert round(lam, 5) == 1.77925


def test_calc_lam_turb2():
    lam = calc_lambda_turb2(1)
    assert lam == 0.2242


def test_calc_lam_rough():
    lam = calc_lambda_rough(1, 1)
    assert round(lam, 5) == 0.77116


def test_calc_lam_turb3():
    lam = calc_lambda_turb3(1)
    assert round(lam, 5) == 12.18494


def test_calc_lam_transition():
    lam = calc_lambda_transition(1, 1, 1)
    assert round(lam, 5) == 23.41445
