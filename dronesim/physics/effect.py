
import numpy as np

class AerialEffects:
    def __init__(self):
        self.reset()

    def reset(self):
        self.rand_acc_xy = 0.0
        self.rand_acc_z = 0.0
        self.rand_acc_a = 0.0

    def applyShakeEffect(self, velvec : np.ndarray , max_noise_magnitude : float = 1e-1, factors : np.ndarray = None, influence_value : float = 0.0):
        #Random shaking Brownian motion
        noise_magnitude = np.random.uniform(0, max_noise_magnitude) * np.clip(influence_value * 1e-1, 0.5, 1.5)
        self.rand_acc_xy += np.random.uniform(0, 2*np.pi)
        self.rand_acc_z += np.random.uniform(0, 2*np.pi)
        self.rand_acc_a += np.random.uniform(0, 2*np.pi)
        a0 = np.cos(self.rand_acc_xy) * noise_magnitude
        a1 = np.sin(self.rand_acc_xy) * noise_magnitude
        a2 = np.sin(self.rand_acc_z) * 1.8 * noise_magnitude
        a3 = np.sin(self.rand_acc_a) * 0.01 * noise_magnitude
        print(a0, a1, a2, a3)

