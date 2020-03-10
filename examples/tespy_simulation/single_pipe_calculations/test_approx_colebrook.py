import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import root

from tespy.tools.helpers import lamb

eps = 0.01 * 1e-3
D = 0.25
print('Ratio e/d=', eps / D)

lam = {'Re': [], 'l0': [], 'l1': [], 'l2': [], 'l3': [], 'l4': [], 'l5': []}

for Re in [10000, 20000, 30000, 70000, 100000]:
    lamb0 = 0.07 * Re ** (-0.13) * D ** (-0.14)
    lamb1 = 1.325 / (np.log(eps / (3.7 * D) + 5.74 / (Re ** 0.9))) ** 2
    lamb2 = 0.25 * 1 / (np.log10(15 / Re + eps / (3.715 * D))) ** 2
    lamb3 = 0.25 / (np.log10(eps / (3.7 * D) + 5.74 / (Re ** 0.9))) ** 2

    def f(x):
        return -2 * np.log10(
            (2.51 / (Re * np.sqrt(x))) + (eps / (3.71 * D))
        ) - 1.0 / np.sqrt(x)

    lamb4 = root(f, 0.0002)['x'][0]

    lamb_tespy = lamb(Re, eps, D)

    lam['Re'].append(Re)
    lam['l0'].append(lamb0)
    lam['l1'].append(lamb1)
    lam['l2'].append(lamb2)
    lam['l3'].append(lamb3)
    lam['l4'].append(lamb4)
    lam['l5'].append(lamb_tespy)

ll = pd.DataFrame(lam)
ll = ll.set_index('Re')
print(ll['l5'])
fig, ax = plt.subplots(figsize=(6, 6))
ll[['l0', 'l1', 'l2', 'l3', 'l4', 'l5']].plot(marker='.', ax=ax)
ax.set_ylabel('$\lambda$')
fig.savefig('test_approx_colebrook.pdf')
