import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os
import json

class EKFAnalyzerWindow:
    def __init__(self, parent, fonts, colors):
        self.window = tk.Toplevel(parent)
        self.window.title("Extended Kalman Filter - SOC Estimation Analyzer")
        self.window.geometry("1100x800")
        self.window.minsize(900, 600)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.fonts = fonts
        self.colors = colors
        self.results_df = None
        
        self.live_active = False
        self.live_data = {'t': [], 'soc': [], 'v_meas': [], 'v_est': []}
        self.plot_update_id = None
        
        # Default 7th Order Polynomial Coefficients (from SOC^7 down to Constant)
        self.default_poly_coeffs = {
            "OCV": [-23.60229, 141.34077, -314.92282, 345.34531, -200.15462, 60.21383, -7.88447, 3.2377],
            "R_int": [-0.00634, 0.09353, -0.28992, 0.41465, -0.32647, 0.1455, -0.03427, 0.00573],
            "R1": [-0.66827, 3.08032, -5.81819, 5.79793, -3.27616, 1.05147, -0.18008, 0.01513],
            "C1": [-19033600.0, 72281100.0, -111014000.0, 88589200.0, -39108800.0, 9265300.0, -1005830.0, 47718.90713],
            "R2": [-0.66827, 3.08032, -5.81819, 5.79793, -3.27616, 1.05147, -0.18008, 0.01513],
            "C2": [-19033600.0, 72281100.0, -111014000.0, 88589200.0, -39108800.0, 9265300.0, -1005830.0, 47718.90713]
        }
        
        self.poly_coeffs = {k: list(v) for k, v in self.default_poly_coeffs.items()}
        
        self._build_ui()

    def _build_ui(self):
        # Top Control Frame
        control_frame = tk.Frame(self.window, bg=self.colors["bg_light"], pady=10, padx=10, relief="groove", borderwidth=1)
        control_frame.pack(side=tk.TOP, fill="x")

        # Parameters
        param_frame = tk.LabelFrame(control_frame, text="Battery & EKF Parameters", bg=self.colors["bg_light"], font=self.fonts["header"])
        param_frame.pack(side=tk.LEFT, fill="y", padx=10)

        self.param_vars = {
            "Capacity (Ah)": tk.StringVar(value="2.6"),
            "Initial SOC": tk.StringVar(value="1.0"),
            "Efficiency": tk.StringVar(value="0.98"),
            "Sample Time (s)": tk.StringVar(value="1.0"),
            "Process Noise Q": tk.StringVar(value="1e-5"),
            "Meas. Noise R": tk.StringVar(value="5e-4"),
            "Initial Cov. P": tk.StringVar(value="0.1"),
            "Parallel Cells (Np)": tk.StringVar(value="1"),
        }
        
        row = 0
        col = 0
        for name, var in self.param_vars.items():
            tk.Label(param_frame, text=name + ":", bg=self.colors["bg_light"], font=self.fonts["normal"]).grid(row=row, column=col, sticky="e", padx=5, pady=2)
            tk.Entry(param_frame, textvariable=var, width=10, font=self.fonts["normal"]).grid(row=row, column=col+1, sticky="w", padx=5, pady=2)
            row += 1
            if row > 3:
                row = 0
                col += 2
            
        self.invert_current_var = tk.BooleanVar(value=False)
        tk.Checkbutton(param_frame, text="Invert Current Sign", variable=self.invert_current_var, bg=self.colors["bg_light"], font=self.fonts["normal"]).grid(row=4, column=0, columnspan=2, sticky="w", padx=5)
        tk.Button(param_frame, text="Advanced Settings ⚙", command=self.open_advanced_settings, bg=self.colors["btn_neutral"], font=self.fonts["button_small"]).grid(row=4, column=2, columnspan=2, sticky="e", padx=5, pady=5)

        # Offline Action Buttons
        action_frame = tk.LabelFrame(control_frame, text="Offline Actions", bg=self.colors["bg_light"], font=self.fonts["header"])
        action_frame.pack(side=tk.LEFT, fill="y", padx=10)

        tk.Button(action_frame, text="1. Download CSV Template", command=self.download_template, bg=self.colors["btn_neutral"], font=self.fonts["button"], width=25).pack(pady=5, padx=10)
        tk.Button(action_frame, text="2. Load Data & Run EKF", command=self.load_and_run, bg=self.colors["btn_connect"], font=self.fonts["button"], width=25).pack(pady=5, padx=10)
        
        self.btn_export = tk.Button(action_frame, text="3. Export EKF Results", command=self.export_results, bg=self.colors["btn_record"], font=self.fonts["button"], width=25, state="disabled")
        self.btn_export.pack(pady=5, padx=10)
        
        # Live Monitoring Buttons
        live_frame = tk.LabelFrame(control_frame, text="Live Serial Monitoring", bg=self.colors["bg_light"], font=self.fonts["header"])
        live_frame.pack(side=tk.LEFT, fill="y", padx=10)
        
        self.btn_live = tk.Button(live_frame, text="Start Live EKF", command=self.toggle_live_ekf, bg=self.colors["btn_record"], font=self.fonts["button"], width=20)
        self.btn_live.pack(pady=5, padx=10)
        
        self.lbl_live_soc = tk.Label(live_frame, text="Live SOC: -- %", font=self.fonts["label_title"], bg=self.colors["bg_light"], fg=self.colors["status_warn"])
        self.lbl_live_soc.pack(pady=2)
        
        self.lbl_live_v = tk.Label(live_frame, text="Min Cell V: -- V", font=self.fonts["mono"], bg=self.colors["bg_light"], fg=self.colors["text_gray"])
        self.lbl_live_v.pack(pady=0)
        
        self.lbl_live_i = tk.Label(live_frame, text="Cell I: -- A", font=self.fonts["mono"], bg=self.colors["bg_light"], fg=self.colors["text_gray"])
        self.lbl_live_i.pack(pady=(0, 5))

        # Plot Frame
        self.plot_frame = tk.Frame(self.window)
        self.plot_frame.pack(side=tk.TOP, fill="both", expand=True, padx=10, pady=10)
        
        # Placeholder text
        self.lbl_placeholder = tk.Label(self.plot_frame, text="Load a valid CSV file to run the simulation and display plots.\n\nNote: In this model, POSITIVE current indicates DISCHARGE.", font=self.fonts["label_title"], fg=self.colors["text_gray"])
        self.lbl_placeholder.pack(expand=True)
        
    def on_close(self):
        if self.live_active:
            self.toggle_live_ekf()
        self.window.destroy()

    def open_advanced_settings(self):
        adv_win = tk.Toplevel(self.window)
        adv_win.title("Advanced Settings - Polynomial Coefficients")
        adv_win.geometry("900x300")
        adv_win.resizable(False, False)
        adv_win.grab_set()  # Make window modal

        frame = tk.Frame(adv_win, padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        # Create Table Headers
        headers = ["Parameter", "x^7", "x^6", "x^5", "x^4", "x^3", "x^2", "x^1", "Constant"]
        for col, h in enumerate(headers):
            tk.Label(frame, text=h, font=self.fonts["header"]).grid(row=0, column=col, padx=5, pady=5)

        # Create Text Boxes for Coefficients
        self.adv_vars = {}
        for row, (param, coeffs) in enumerate(self.poly_coeffs.items(), start=1):
            tk.Label(frame, text=param, font=self.fonts["header"]).grid(row=row, column=0, padx=5, pady=5, sticky="e")
            self.adv_vars[param] = []
            for col, val in enumerate(coeffs, start=1):
                var = tk.StringVar(value=str(val))
                self.adv_vars[param].append(var)
                tk.Entry(frame, textvariable=var, width=11, font=self.fonts["mono_small"]).grid(row=row, column=col, padx=2, pady=2)

        btn_frame = tk.Frame(adv_win, pady=10)
        btn_frame.pack(side=tk.BOTTOM, fill="x", padx=10)
        
        left_btn_frame = tk.Frame(btn_frame)
        left_btn_frame.pack(side=tk.LEFT)
        
        right_btn_frame = tk.Frame(btn_frame)
        right_btn_frame.pack(side=tk.RIGHT)

        def update_ui_from_dict(new_coeffs):
            for param, vars_list in self.adv_vars.items():
                if param in new_coeffs and len(new_coeffs[param]) == len(vars_list):
                    for var, val in zip(vars_list, new_coeffs[param]):
                        var.set(str(val))

        def reset_defaults():
            update_ui_from_dict(self.default_poly_coeffs)
            
        def load_json():
            path = filedialog.askopenfilename(
                filetypes=[("JSON Files", "*.json")],
                title="Load Polynomial Coefficients"
            )
            if path:
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                    update_ui_from_dict(data)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load file:\n{e}", parent=adv_win)
                    
        def save_json():
            path = filedialog.asksaveasfilename(
                initialfile="EKF_Poly_Coeffs.json",
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json")],
                title="Save Polynomial Coefficients"
            )
            if path:
                try:
                    current_data = {}
                    for param, vars_list in self.adv_vars.items():
                        current_data[param] = [float(v.get()) for v in vars_list]
                    with open(path, "w") as f:
                        json.dump(current_data, f, indent=4)
                    messagebox.showinfo("Success", "Coefficients saved to JSON successfully!", parent=adv_win)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file:\n{e}", parent=adv_win)

        def save_settings():
            try:
                for param, vars_list in self.adv_vars.items():
                    self.poly_coeffs[param] = [float(v.get()) for v in vars_list]
                messagebox.showinfo("Success", "Polynomial coefficients updated successfully!", parent=adv_win)
                adv_win.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid input. Please ensure all coefficients are valid numbers.", parent=adv_win)

        tk.Button(left_btn_frame, text="Load JSON", command=load_json, bg=self.colors["btn_connect"], font=self.fonts["button"]).pack(side=tk.LEFT, padx=5)
        tk.Button(left_btn_frame, text="Save JSON", command=save_json, bg=self.colors["btn_connect"], font=self.fonts["button"]).pack(side=tk.LEFT, padx=5)
        tk.Button(left_btn_frame, text="Reset Defaults", command=reset_defaults, bg=self.colors["btn_neutral"], font=self.fonts["button"]).pack(side=tk.LEFT, padx=5)

        tk.Button(right_btn_frame, text="Cancel", command=adv_win.destroy, bg=self.colors["btn_neutral"], font=self.fonts["button"]).pack(side=tk.RIGHT, padx=5)
        tk.Button(right_btn_frame, text="Save Changes", command=save_settings, bg=self.colors["btn_record"], font=self.fonts["button"]).pack(side=tk.RIGHT, padx=5)

    def download_template(self):
        path = filedialog.asksaveasfilename(
            initialfile="EKF_Input_Template.csv",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Save CSV Template"
        )
        if path:
            try:
                # Creating a dummy 10-second discharge at 2.6A
                df = pd.DataFrame({
                    "Time_s": range(0, 11),
                    "Current_A": [2.6] * 11
                })
                df.to_csv(path, index=False)
                messagebox.showinfo("Template Downloaded", f"Successfully saved template to:\n{path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def export_results(self):
        if self.results_df is None:
            return
            
        path = filedialog.asksaveasfilename(
            initialfile="EKF_Estimation_Results.csv",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Export EKF Results"
        )
        if path:
            try:
                self.results_df.to_csv(path, index=False)
                messagebox.showinfo("Success", "Results exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {e}")

    def load_and_run(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV/Excel Files", "*.csv *.xlsx")],
            title="Load Current Profile Data"
        )
        if not path:
            return
            
        try:
            # Parse variables
            cap_ah = float(self.param_vars["Capacity (Ah)"].get())
            init_soc = float(self.param_vars["Initial SOC"].get())
            eff = float(self.param_vars["Efficiency"].get())
            dt = float(self.param_vars["Sample Time (s)"].get())
            
            # Read Data
            if path.endswith(".csv"):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
                
            # Look for Current column
            current_col = None
            for col in df.columns:
                if "current" in col.lower() or col.strip() == "i":
                    current_col = col
                    break
                    
            if not current_col:
                raise ValueError("Could not find a column for Current in the uploaded file.\nPlease name it 'Current_A' or similar.")
                
            # Adjust current to single cell level
            current_profile = df[current_col].values 
            np_cells = float(self.param_vars["Parallel Cells (Np)"].get())
            current_profile = current_profile / np_cells
            
            # Run EKF simulation
            self.run_ekf_algorithm(current_profile, cap_ah, init_soc, eff, dt)
            
        except Exception as e:
            messagebox.showerror("Simulation Error", f"An error occurred:\n\n{str(e)}")

    def run_ekf_algorithm(self, current_profile, q0_ah, init_soc, eff, deltaT):
        N = len(current_profile)
        Q0 = q0_ah * 3600.0  # Ah to Amp-Sec
        
        # Initializations matching MATLAB code
        X = np.zeros((3, N))
        X[:, 0] = [init_soc, 0, 0]
        
        X_update = np.zeros((3, N))
        X_update[:, 0] = [init_soc, 0, 0]
        
        X_predict = np.zeros((3, N))
        
        p_val = float(self.param_vars["Initial Cov. P"].get())
        P = np.diag([p_val, p_val, p_val])
        Q = float(self.param_vars["Process Noise Q"].get())
        R = float(self.param_vars["Meas. Noise R"].get())
        
        UL = np.zeros((1, N))
        UL[0, 0] = 4.2375
        
        VL_store = np.zeros((1, N))
        
        # Main Loop
        for t in range(1, N):
            i = current_profile[t]
            
            # -------------------------------------------------------------
            # TRUE MODEL SIMULATION (Loop 1 equivalent)
            # -------------------------------------------------------------
            SOC = X[0, t-1]
            R_int = np.polyval(self.poly_coeffs["R_int"], SOC)
            R1 = np.polyval(self.poly_coeffs["R1"], SOC)
            C1 = np.polyval(self.poly_coeffs["C1"], SOC)
            R2 = np.polyval(self.poly_coeffs["R2"], SOC)
            C2 = np.polyval(self.poly_coeffs["C2"], SOC)
            
            tau1 = R1 * C1
            tau2 = R2 * C2
            
            A = np.array([
                [1, 0, 0],
                [0, np.exp(-deltaT/tau1), 0],
                [0, 0, np.exp(-deltaT/tau2)]
            ])
            
            B = np.array([
                [-eff * deltaT / Q0],
                [R1 * (1 - np.exp(-deltaT/tau1))],
                [R2 * (1 - np.exp(-deltaT/tau2))]
            ])
            
            X[:, [t]] = A @ X[:, [t-1]] + B * i + (np.sqrt(Q) * np.random.randn(3, 1))
            V_RC1 = X[1, t]
            V_RC2 = X[2, t]
            
            Uocv = np.polyval(self.poly_coeffs["OCV"], SOC)
            UL[0, t] = Uocv - V_RC1 - V_RC2 - i * R_int + (np.sqrt(Q) * np.random.randn())
            
            # -------------------------------------------------------------
            # EKF ALGORITHM (Loop 2 equivalent)
            # -------------------------------------------------------------
            SOC_upd = X_update[0, t-1]
            R_int_ekf = np.polyval(self.poly_coeffs["R_int"], SOC_upd)
            R1_ekf = np.polyval(self.poly_coeffs["R1"], SOC_upd)
            C1_ekf = np.polyval(self.poly_coeffs["C1"], SOC_upd)
            R2_ekf = np.polyval(self.poly_coeffs["R2"], SOC_upd)
            C2_ekf = np.polyval(self.poly_coeffs["C2"], SOC_upd)
            
            tau1_ekf = R1_ekf * C1_ekf
            tau2_ekf = R2_ekf * C2_ekf
            
            A_ekf = np.array([
                [1, 0, 0],
                [0, np.exp(-deltaT/tau1_ekf), 0],
                [0, 0, np.exp(-deltaT/tau2_ekf)]
            ])
            
            B_ekf = np.array([
                [-deltaT * eff / Q0],
                [R1_ekf * (1 - np.exp(-deltaT/tau1_ekf))],
                [R2_ekf * (1 - np.exp(-deltaT/tau2_ekf))]
            ])
            
            X_predict[:, [t]] = A_ekf @ X_update[:, [t-1]] + B_ekf * i
            SOC_pred = X_predict[0, t]
            VRC1_pred = X_predict[1, t]
            VRC2_pred = X_predict[2, t]
            
            Uocv_pred = np.polyval(self.poly_coeffs["OCV"], SOC_pred)
            
            VL = Uocv_pred - VRC1_pred - VRC2_pred - i * R_int_ekf
            VL_store[0, t] = VL
            
            P1 = A_ekf @ P @ A_ekf.T + np.diag([Q, Q, Q])
            
            Cu = np.polyval(np.polyder(self.poly_coeffs["OCV"]), SOC_pred)
            C_mat = np.array([[Cu, -1.0, -1.0]])
            
            S = C_mat @ P1 @ C_mat.T + R
            K = P1 @ C_mat.T @ np.linalg.inv(S)
            
            X_update[:, [t]] = X_predict[:, [t]] + K * (UL[0, t] - VL)
            X_update[0, t] = np.clip(X_update[0, t], 0.0, 1.0) # Clamp SOC between 0% and 100%
            P = P1 - K @ C_mat @ P1

        # Save results for exporting
        time_array = np.arange(N) * deltaT
        self.results_df = pd.DataFrame({
            "Time_s": time_array,
            "Current_A": current_profile,
            "True_SOC": X[0, :],
            "EKF_SOC": X_update[0, :],
            "True_Voltage_V": UL[0, :],
            "Estimated_Voltage_V": VL_store[0, :]
        })
        
        self.btn_export.config(state="normal")
        self.plot_results(time_array, X[0, :], X_update[0, :], UL[0, :], VL_store[0, :])

    def plot_results(self, t, soc_true, soc_ekf, v_true, v_ekf):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
            
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        
        ax1.plot(t, soc_true * 100, 'g', label='True Simulated SOC')
        ax1.plot(t, soc_ekf * 100, 'b--', label='EKF Estimated SOC')
        ax1.set_ylabel('State of Charge [%]')
        ax1.set_title('SOC Estimation using Extended Kalman Filter')
        ax1.grid(True)
        ax1.legend()
        
        ax2.plot(t, v_true, 'g', label='True Terminal Voltage')
        ax2.plot(t, v_ekf, 'r--', label='Estimated Terminal Voltage')
        ax2.set_xlabel('Time [s]')
        ax2.set_ylabel('Voltage [V]')
        ax2.grid(True)
        ax2.legend()
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        toolbar = NavigationToolbar2Tk(canvas, self.plot_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
    # ---------------------------------------------------------------------
    # LIVE EKF FUNCTIONALITY
    # ---------------------------------------------------------------------
    def toggle_live_ekf(self):
        if not self.live_active:
            self.live_active = True
            self.btn_live.config(text="Stop Live EKF", bg=self.colors["btn_disconnect"])
            self.lbl_live_soc.config(text="Live SOC: Initializing...", fg=self.colors["status_ok"])
            
            # Initialize Matrix state
            self.cap_ah = float(self.param_vars["Capacity (Ah)"].get())
            self.init_soc = float(self.param_vars["Initial SOC"].get())
            self.eff = float(self.param_vars["Efficiency"].get())
            self.Q0 = self.cap_ah * 3600.0
            
            self.X_update = np.array([[self.init_soc], [0.0], [0.0]])
            p_val = float(self.param_vars["Initial Cov. P"].get())
            self.P = np.diag([p_val, p_val, p_val])
            self.Q_noise = float(self.param_vars["Process Noise Q"].get())
            self.R_noise = float(self.param_vars["Meas. Noise R"].get())
            
            self.start_time = None
            self.last_update_time = None
            self.acc_current = []
            self.acc_voltage = []
            self.live_data = {'t': [], 'soc': [], 'v_meas': [], 'v_est': []}
            
            # Setup blank canvas for Live plot
            for widget in self.plot_frame.winfo_children():
                widget.destroy()
                
            self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
            self.ax1.set_ylabel('State of Charge [%]')
            self.ax1.set_title('Live EKF SOC Estimation')
            self.ax1.grid(True)
            self.ax2.set_xlabel('Time [s]')
            self.ax2.set_ylabel('Voltage [V]')
            self.ax2.grid(True)
            
            self.line_soc, = self.ax1.plot([], [], 'b-', label='EKF Estimated SOC')
            self.line_v_meas, = self.ax2.plot([], [], 'g-', label='Measured Terminal Voltage')
            self.line_v_est, = self.ax2.plot([], [], 'r--', label='Estimated Terminal Voltage')
            
            self.ax1.legend(loc='upper right')
            self.ax2.legend(loc='upper right')
            self.fig.tight_layout()
            
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
            # Begin UI refresh loop
            self.update_live_plot()
            
        else:
            self.live_active = False
            self.btn_live.config(text="Start Live EKF", bg=self.colors["btn_record"])
            self.lbl_live_soc.config(text="Live SOC: -- %", fg=self.colors["status_warn"])
            self.lbl_live_v.config(text="Min Cell V: -- V")
            self.lbl_live_i.config(text="Cell I: -- A")
            if self.plot_update_id:
                self.window.after_cancel(self.plot_update_id)
                self.plot_update_id = None
                
            # Pass results for export
            if len(self.live_data['t']) > 0:
                self.results_df = pd.DataFrame({
                    "Time_s": self.live_data['t'],
                    "EKF_SOC": self.live_data['soc'],
                    "Measured_Voltage_V": self.live_data['v_meas'],
                    "Estimated_Voltage_V": self.live_data['v_est']
                })
                self.btn_export.config(state="normal")
                messagebox.showinfo("Live Monitoring Stopped", "The live session has finished. You can now export the recorded estimations to CSV.")

    def push_live_data(self, current_A, voltage_V, timestamp):
        if not self.live_active:
            return
            
        np_cells = float(self.param_vars["Parallel Cells (Np)"].get())
        cell_current_A = current_A / np_cells
            
        self.lbl_live_v.config(text=f"Min Cell V: {voltage_V:.3f} V")
        self.lbl_live_i.config(text=f"Cell I: {cell_current_A:.2f} A (Pack: {current_A:.2f}A)")
        
        if self.invert_current_var.get():
            cell_current_A = -cell_current_A
            
        if self.start_time is None:
            self.start_time = timestamp
            self.last_update_time = timestamp
            self.acc_current = []
            self.acc_voltage = []
            return
            
        target_dt = float(self.param_vars["Sample Time (s)"].get())
        self.acc_current.append(cell_current_A)
        self.acc_voltage.append(voltage_V)
        
        # Wait until sufficient time equivalent to `dt` has passed to ensure matrix stability
        actual_dt = timestamp - self.last_update_time
        if actual_dt >= target_dt:
            self.last_update_time = timestamp
            avg_i = np.mean(self.acc_current)
            avg_v = np.mean(self.acc_voltage)
            
            self.acc_current = []
            self.acc_voltage = []
            
            # Perform 1 Step prediction & update
            self.step_live_ekf(avg_i, avg_v, actual_dt, timestamp)
            
    def step_live_ekf(self, i, VL, deltaT, timestamp):
        SOC_upd = self.X_update[0, 0]
        
        R_int_ekf = np.polyval(self.poly_coeffs["R_int"], SOC_upd)
        R1_ekf = np.polyval(self.poly_coeffs["R1"], SOC_upd)
        C1_ekf = np.polyval(self.poly_coeffs["C1"], SOC_upd)
        R2_ekf = np.polyval(self.poly_coeffs["R2"], SOC_upd)
        C2_ekf = np.polyval(self.poly_coeffs["C2"], SOC_upd)
        
        tau1_ekf = R1_ekf * C1_ekf
        tau2_ekf = R2_ekf * C2_ekf
        
        A_ekf = np.array([
            [1, 0, 0],
            [0, np.exp(-deltaT/tau1_ekf), 0],
            [0, 0, np.exp(-deltaT/tau2_ekf)]
        ])
        
        B_ekf = np.array([
            [-deltaT * self.eff / self.Q0],
            [R1_ekf * (1 - np.exp(-deltaT/tau1_ekf))],
            [R2_ekf * (1 - np.exp(-deltaT/tau2_ekf))]
        ])
        
        X_predict = A_ekf @ self.X_update + B_ekf * i
        SOC_pred = X_predict[0, 0]
        VRC1_pred = X_predict[1, 0]
        VRC2_pred = X_predict[2, 0]
        
        Uocv_pred = np.polyval(self.poly_coeffs["OCV"], SOC_pred)
        VL_est = Uocv_pred - VRC1_pred - VRC2_pred - i * R_int_ekf
        
        P1 = A_ekf @ self.P @ A_ekf.T + np.diag([self.Q_noise, self.Q_noise, self.Q_noise])
        Cu = np.polyval(np.polyder(self.poly_coeffs["OCV"]), SOC_pred)
        C_mat = np.array([[Cu, -1.0, -1.0]])
        
        S = C_mat @ P1 @ C_mat.T + self.R_noise
        K = P1 @ C_mat.T @ np.linalg.inv(S)
        
        self.X_update = X_predict + K * (VL - VL_est)
        self.X_update[0, 0] = np.clip(self.X_update[0, 0], 0.0, 1.0) # Clamp SOC between 0% and 100%
        self.P = P1 - K @ C_mat @ P1
        
        t_elapsed = timestamp - self.start_time
        self.live_data['t'].append(t_elapsed)
        self.live_data['soc'].append(self.X_update[0, 0])
        self.live_data['v_meas'].append(VL)
        self.live_data['v_est'].append(VL_est)
        
        self.lbl_live_soc.config(text=f"Live SOC: {self.X_update[0, 0]*100:.2f} %")
        
    def update_live_plot(self):
        if not self.live_active:
            return
            
        if len(self.live_data['t']) > 0:
            self.line_soc.set_data(self.live_data['t'], np.array(self.live_data['soc']) * 100)
            self.line_v_meas.set_data(self.live_data['t'], self.live_data['v_meas'])
            self.line_v_est.set_data(self.live_data['t'], self.live_data['v_est'])
            
            self.ax1.relim()
            self.ax1.autoscale_view()
            self.ax2.relim()
            self.ax2.autoscale_view()
            self.canvas.draw()
            
        # Reschedule plot update (1 Hz UI refresh to conserve system resources)
        self.plot_update_id = self.window.after(1000, self.update_live_plot)