import numpy as np

class BatteryEKF:
    """
    Extended Kalman Filter for Battery SOC Estimation using a 1-RC equivalent circuit model.
    """
    def __init__(self, capacity_ah, r0=0.01, r1=0.01, c1=1000):
        # Battery Parameters
        self.Q = capacity_ah * 3600.0  # Total capacity in Ampere-seconds (Coulombs)
        self.R0 = r0  # Ohmic resistance
        self.R1 = r1  # Polarization resistance
        self.C1 = c1  # Polarization capacitance
        
        # State Vector: x = [SOC, V_rc]^T
        # Initialize at 100% SOC and 0V RC voltage
        self.x = np.array([[1.0], 
                           [0.0]])
        
        # Error Covariance Matrix (P)
        self.P = np.array([[1e-4, 0], 
                           [0, 1e-4]])
        
        # Process Noise Covariance (Q_noise) - Model uncertainty
        self.Q_noise = np.array([[1e-6, 0], 
                                 [0, 1e-5]])
        
        # Measurement Noise Covariance (R_noise) - Sensor noise
        self.R_noise = np.array([[1e-2]])
        
        # Default Polynomial Coefficients for OCV(SOC)
        # Highest degree first. Users should call set_ocv_lookup_table() to override this.
        self.ocv_poly_coeffs = np.array([3.4, 0]) 

    def set_ocv_lookup_table(self, soc_points, ocv_points, degree=5):
        """
        Feeds the lookup table into the EKF. Fits an n-th degree polynomial.
        
        :param soc_points: List or array of SOC values (e.g. 0.0 to 1.0)
        :param ocv_points: List or array of corresponding OCV voltages
        :param degree: The degree of the polynomial to fit
        """
        # np.polyfit returns coefficients starting with the highest power
        self.ocv_poly_coeffs = np.polyfit(soc_points, ocv_points, degree)

    def _get_ocv_and_derivative(self, soc):
        """
        Calculates the estimated OCV and its derivative d(OCV)/d(SOC) at a given SOC
        using the fitted polynomial.
        """
        # Constrain SOC between 0% and 100% for mathematical stability
        soc = np.clip(soc, 0.0, 1.0)
        
        # Calculate OCV from polynomial
        ocv = np.polyval(self.ocv_poly_coeffs, soc)
        
        # Calculate derivative of the polynomial
        poly_deriv = np.polyder(self.ocv_poly_coeffs)
        d_ocv = np.polyval(poly_deriv, soc)
        
        return ocv, d_ocv

    def update(self, current, voltage, dt):
        """
        Perform one step of the EKF (Prediction and Correction).
        
        IMPORTANT SIGN CONVENTION:
        current > 0 : Charging (SOC increases)
        current < 0 : Discharging (SOC decreases)
        
        :param current: Measured current in Amperes
        :param voltage: Measured terminal voltage in Volts
        :param dt: Time step since last update in seconds
        :return: (Estimated SOC, Estimated V_rc)
        """
        # Extract previous states
        soc_prev = self.x[0, 0]
        vrc_prev = self.x[1, 0]
        
        # ==========================================
        # 1. PREDICTION STEP (Time Update)
        # ==========================================
        # SOC_k = SOC_{k-1} + (I * dt) / Q
        soc_pred = soc_prev + (current * dt) / self.Q
        
        # Vrc_k = exp(-dt/RC) * Vrc_{k-1} + R*(1 - exp(-dt/RC)) * I
        exp_term = np.exp(-dt / (self.R1 * self.C1))
        vrc_pred = exp_term * vrc_prev + self.R1 * (1 - exp_term) * current
        
        x_pred = np.array([[soc_pred], [vrc_pred]])
        
        # State Transition Jacobian Matrix (A)
        A = np.array([[1.0, 0.0], 
                      [0.0, exp_term]])
        
        # Predict Error Covariance: P_pred = A * P * A^T + Q_noise
        P_pred = A @ self.P @ A.T + self.Q_noise
        
        # ==========================================
        # 2. CORRECTION STEP (Measurement Update)
        # ==========================================
        ocv_pred, d_ocv = self._get_ocv_and_derivative(soc_pred)
        
        # Expected Voltage: V = OCV(SOC) + V_rc + R0 * I
        v_est = ocv_pred + vrc_pred + self.R0 * current
        
        # Measurement Jacobian Matrix (H)
        H = np.array([[d_ocv, 1.0]])
        
        # Residual / Innovation (y)
        y = np.array([[voltage - v_est]])
        
        # Innovation Covariance (S)
        S = H @ P_pred @ H.T + self.R_noise
        
        # Kalman Gain (K)
        K = P_pred @ H.T @ np.linalg.inv(S)
        
        # Update State with Measurement
        self.x = x_pred + K @ y
        
        # Constrain physical limits
        self.x[0, 0] = np.clip(self.x[0, 0], 0.0, 1.0)
        
        # Update Covariance
        I_mat = np.eye(2)
        self.P = (I_mat - K @ H) @ P_pred
        
        return self.x[0, 0]