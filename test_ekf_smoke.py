import numpy as np
from bms_monitor.ekf_soc import BatteryEKF

def run_smoke_test():
    print("--- EKF SOC Smoke Test ---")
    
    # 1. Initialize EKF for a 50Ah Battery
    ekf = BatteryEKF(capacity_ah=50.0, r0=0.015, r1=0.01, c1=1000)
    
    # 2. Feed Lookup Table (SOC points vs OCV points)
    soc_lut = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ocv_lut = np.array([3.0, 3.3, 3.45, 3.55, 3.6, 3.7, 3.8, 3.9, 4.0, 4.1, 4.2])
    
    print("Fitting LUT to 5th degree polynomial...")
    ekf.set_ocv_lookup_table(soc_lut, ocv_lut, degree=5)
    print(f"Generated Polynomial Coefficients: {ekf.ocv_poly_coeffs}")
    
    # 3. Simulate Discharging Process
    print("\nStarting Simulation: 100% SOC -> Heavy Discharge (-20A)")
    
    # Force initial state to 100%
    current_soc = 1.0 
    dt = 1.0  # 1 second step
    
    print(f"Time 0s | Current: 0A   | Est SOC: {current_soc*100:.2f}%")
    
    # Simulate 5 steps of 1-second discharging at 20A
    for step in range(1, 6):
        # SIMULATE MEASUREMENTS:
        # Current must be NEGATIVE for discharge in this convention
        meas_current = -20.0 
        
        # Fake a terminal voltage measurement dropping under load
        meas_voltage = 4.15 - (step * 0.01) 
        
        # Update EKF
        current_soc = ekf.update(current=meas_current, voltage=meas_voltage, dt=dt)
        
        print(f"Time {step}s | Current: {meas_current}A | Est SOC: {current_soc*100:.4f}% | Voltage: {meas_voltage:.2f}V")
        
    # Assertions for the smoke test
    if current_soc < 1.0:
        print("\n✅ SMOKE TEST PASSED: SOC successfully decreased during discharge!")
    else:
        print("\n❌ SMOKE TEST FAILED: SOC increased or didn't change during discharge!")

if __name__ == "__main__":
    run_smoke_test()