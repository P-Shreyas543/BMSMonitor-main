import json
import tkinter as tk
from tkinter import filedialog, messagebox

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


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
        self.live_data = {"t": [], "soc": [], "v_meas": [], "v_est": [], "residual": []}
        self.plot_update_id = None

        self.ocv_soc_table = pd.DataFrame(
            {
                "SOC": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                "OCV": [3.2377, 3.4718, 3.5874, 3.6419, 3.6836, 3.7360, 3.8040, 3.8931, 4.0087, 4.1397, 4.2377],
            }
        )
        self._sanitize_ocv_soc_table()

        self._build_ui()

    def _build_ui(self):
        control_frame = tk.Frame(self.window, bg=self.colors["bg_light"], pady=10, padx=10, relief="groove", borderwidth=1)
        control_frame.pack(side=tk.TOP, fill="x")

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
            "R0 Internal (ohm)": tk.StringVar(value="0.00573"),
            "R1 (ohm)": tk.StringVar(value="0.01513"),
            "C1 (F)": tk.StringVar(value="47718.9"),
            "R2 (ohm)": tk.StringVar(value="0.01513"),
            "C2 (F)": tk.StringVar(value="47718.9"),
        }

        for index, (name, var) in enumerate(self.param_vars.items()):
            row = index % 5
            col = (index // 5) * 2
            tk.Label(param_frame, text=name + ":", bg=self.colors["bg_light"], font=self.fonts["normal"]).grid(row=row, column=col, sticky="e", padx=5, pady=2)
            tk.Entry(param_frame, textvariable=var, width=10, font=self.fonts["normal"]).grid(row=row, column=col + 1, sticky="w", padx=5, pady=2)

        self.invert_current_var = tk.BooleanVar(value=False)
        tk.Checkbutton(param_frame, text="Invert Current Sign", variable=self.invert_current_var, bg=self.colors["bg_light"], font=self.fonts["normal"]).grid(row=5, column=0, columnspan=2, sticky="w", padx=5)
        tk.Button(param_frame, text="OCV/SOC Table", command=self.open_advanced_settings, bg=self.colors["btn_neutral"], font=self.fonts["button_small"]).grid(row=5, column=2, columnspan=2, sticky="e", padx=5, pady=5)

        action_frame = tk.LabelFrame(control_frame, text="Offline Actions", bg=self.colors["bg_light"], font=self.fonts["header"])
        action_frame.pack(side=tk.LEFT, fill="y", padx=10)
        tk.Button(action_frame, text="1. Download CSV Template", command=self.download_template, bg=self.colors["btn_neutral"], font=self.fonts["button"], width=25).pack(pady=5, padx=10)
        tk.Button(action_frame, text="2. Load Data & Run EKF", command=self.load_and_run, bg=self.colors["btn_connect"], font=self.fonts["button"], width=25).pack(pady=5, padx=10)
        self.btn_export = tk.Button(action_frame, text="3. Export EKF Results", command=self.export_results, bg=self.colors["btn_record"], font=self.fonts["button"], width=25, state="disabled")
        self.btn_export.pack(pady=5, padx=10)

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

        self.plot_frame = tk.Frame(self.window)
        self.plot_frame.pack(side=tk.TOP, fill="both", expand=True, padx=10, pady=10)
        self.lbl_placeholder = tk.Label(self.plot_frame, text="Load a CSV with current and cell voltage to run EKF.\n\nPositive current indicates discharge.", font=self.fonts["label_title"], fg=self.colors["text_gray"])
        self.lbl_placeholder.pack(expand=True)

    def on_close(self):
        if self.live_active:
            self.toggle_live_ekf()
        self.window.destroy()

    def _sanitize_ocv_soc_table(self):
        table = self.ocv_soc_table[["SOC", "OCV"]].copy()
        table["SOC"] = pd.to_numeric(table["SOC"], errors="coerce")
        table["OCV"] = pd.to_numeric(table["OCV"], errors="coerce")
        table = table.dropna()
        table.loc[table["SOC"] > 1.0, "SOC"] = table.loc[table["SOC"] > 1.0, "SOC"] / 100.0
        table = table[(table["SOC"] >= 0.0) & (table["SOC"] <= 1.0)]
        table = table.sort_values("SOC").drop_duplicates("SOC")
        if len(table) < 2:
            raise ValueError("The OCV/SOC table must contain at least two valid rows.")
        self.ocv_soc_table = table.reset_index(drop=True)

    def _read_ocv_soc_table(self, path):
        if path.lower().endswith(".csv"):
            raw = pd.read_csv(path)
        elif path.lower().endswith((".xlsx", ".xls")):
            raw = pd.read_excel(path)
        else:
            with open(path, "r", encoding="utf-8") as file_handle:
                data = json.load(file_handle)
            raw = pd.DataFrame(data)

        soc_col = next((col for col in raw.columns if "soc" in col.lower()), None)
        ocv_col = next((col for col in raw.columns if "ocv" in col.lower() or "voltage" in col.lower()), None)
        if not soc_col or not ocv_col:
            raise ValueError("Table must include SOC and OCV columns.")
        table = raw[[soc_col, ocv_col]].rename(columns={soc_col: "SOC", ocv_col: "OCV"})
        old_table = self.ocv_soc_table
        self.ocv_soc_table = table
        self._sanitize_ocv_soc_table()
        table = self.ocv_soc_table
        self.ocv_soc_table = old_table
        return table

    def _table_from_adv_vars(self):
        rows = []
        for soc_var, ocv_var in self.adv_table_vars:
            soc_text = soc_var.get().strip()
            ocv_text = ocv_var.get().strip()
            if not soc_text and not ocv_text:
                continue
            rows.append({"SOC": float(soc_text), "OCV": float(ocv_text)})
        old_table = self.ocv_soc_table
        self.ocv_soc_table = pd.DataFrame(rows)
        self._sanitize_ocv_soc_table()
        table = self.ocv_soc_table
        self.ocv_soc_table = old_table
        return table

    def open_advanced_settings(self):
        adv_win = tk.Toplevel(self.window)
        adv_win.title("Advanced Settings - OCV/SOC Lookup Table")
        adv_win.geometry("620x520")
        adv_win.grab_set()

        frame = tk.Frame(adv_win, padx=10, pady=10)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="SOC may be 0-1 or 0-100. OCV must be single-cell open-circuit voltage.", font=self.fonts["normal"]).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        for col, header in enumerate(["#", "SOC", "OCV (V)"]):
            tk.Label(frame, text=header, font=self.fonts["header"]).grid(row=1, column=col, padx=5, pady=5)

        self.adv_table_vars = []
        for index in range(20):
            row_data = self.ocv_soc_table.iloc[index] if index < len(self.ocv_soc_table) else None
            soc_var = tk.StringVar(value="" if row_data is None else f"{row_data['SOC']:.6g}")
            ocv_var = tk.StringVar(value="" if row_data is None else f"{row_data['OCV']:.6g}")
            self.adv_table_vars.append((soc_var, ocv_var))
            tk.Label(frame, text=str(index + 1), font=self.fonts["normal"]).grid(row=index + 2, column=0, padx=5, pady=2)
            tk.Entry(frame, textvariable=soc_var, width=16, font=self.fonts["mono"]).grid(row=index + 2, column=1, padx=5, pady=2)
            tk.Entry(frame, textvariable=ocv_var, width=16, font=self.fonts["mono"]).grid(row=index + 2, column=2, padx=5, pady=2)

        btn_frame = tk.Frame(adv_win, pady=10)
        btn_frame.pack(side=tk.BOTTOM, fill="x", padx=10)
        left_btn_frame = tk.Frame(btn_frame)
        left_btn_frame.pack(side=tk.LEFT)
        right_btn_frame = tk.Frame(btn_frame)
        right_btn_frame.pack(side=tk.RIGHT)

        def update_ui_from_table(table):
            for index, (soc_var, ocv_var) in enumerate(self.adv_table_vars):
                if index < len(table):
                    soc_var.set(str(table.iloc[index]["SOC"]))
                    ocv_var.set(str(table.iloc[index]["OCV"]))
                else:
                    soc_var.set("")
                    ocv_var.set("")

        def load_table():
            path = filedialog.askopenfilename(filetypes=[("Table Files", "*.csv *.xlsx *.json")], title="Load OCV/SOC Lookup Table")
            if path:
                try:
                    update_ui_from_table(self._read_ocv_soc_table(path))
                except Exception as exc:
                    messagebox.showerror("Error", f"Failed to load file:\n{exc}", parent=adv_win)

        def save_csv():
            path = filedialog.asksaveasfilename(initialfile="OCV_SOC_Table.csv", defaultextension=".csv", filetypes=[("CSV Files", "*.csv")], title="Save OCV/SOC Lookup Table")
            if path:
                try:
                    self._table_from_adv_vars().to_csv(path, index=False)
                    messagebox.showinfo("Success", "Lookup table saved successfully!", parent=adv_win)
                except Exception as exc:
                    messagebox.showerror("Error", f"Failed to save file:\n{exc}", parent=adv_win)

        def save_settings():
            try:
                self.ocv_soc_table = self._table_from_adv_vars()
                self._sanitize_ocv_soc_table()
                messagebox.showinfo("Success", "OCV/SOC lookup table updated successfully!", parent=adv_win)
                adv_win.destroy()
            except Exception as exc:
                messagebox.showerror("Error", str(exc), parent=adv_win)

        tk.Button(left_btn_frame, text="Load Table", command=load_table, bg=self.colors["btn_connect"], font=self.fonts["button"]).pack(side=tk.LEFT, padx=5)
        tk.Button(left_btn_frame, text="Save CSV", command=save_csv, bg=self.colors["btn_connect"], font=self.fonts["button"]).pack(side=tk.LEFT, padx=5)
        tk.Button(right_btn_frame, text="Cancel", command=adv_win.destroy, bg=self.colors["btn_neutral"], font=self.fonts["button"]).pack(side=tk.RIGHT, padx=5)
        tk.Button(right_btn_frame, text="Save Changes", command=save_settings, bg=self.colors["btn_record"], font=self.fonts["button"]).pack(side=tk.RIGHT, padx=5)

    def _normalize_soc(self, soc):
        soc = float(soc)
        if soc > 1.0:
            soc /= 100.0
        return float(np.clip(soc, 0.0, 1.0))

    def _ocv_from_soc(self, soc):
        soc_values = self.ocv_soc_table["SOC"].to_numpy(dtype=float)
        ocv_values = self.ocv_soc_table["OCV"].to_numpy(dtype=float)
        return float(np.interp(np.clip(soc, 0.0, 1.0), soc_values, ocv_values))

    def _docv_dsoc(self, soc):
        soc_values = self.ocv_soc_table["SOC"].to_numpy(dtype=float)
        ocv_values = self.ocv_soc_table["OCV"].to_numpy(dtype=float)
        gradients = np.gradient(ocv_values, soc_values)
        return float(np.interp(np.clip(soc, 0.0, 1.0), soc_values, gradients))

    def _soc_from_ocv(self, ocv):
        table = self.ocv_soc_table.sort_values("OCV")
        return float(np.interp(float(ocv), table["OCV"], table["SOC"]))

    def _ecm_params(self):
        return {
            "R0": max(float(self.param_vars["R0 Internal (ohm)"].get()), 1e-9),
            "R1": max(float(self.param_vars["R1 (ohm)"].get()), 1e-9),
            "C1": max(float(self.param_vars["C1 (F)"].get()), 1e-9),
            "R2": max(float(self.param_vars["R2 (ohm)"].get()), 1e-9),
            "C2": max(float(self.param_vars["C2 (F)"].get()), 1e-9),
        }

    def _state_matrices(self, deltaT, eff, q0_as):
        params = self._ecm_params()
        tau1 = max(params["R1"] * params["C1"], 1e-9)
        tau2 = max(params["R2"] * params["C2"], 1e-9)
        a1 = np.exp(-deltaT / tau1)
        a2 = np.exp(-deltaT / tau2)
        A = np.array([[1.0, 0.0, 0.0], [0.0, a1, 0.0], [0.0, 0.0, a2]])
        B = np.array([[-deltaT * eff / q0_as], [params["R1"] * (1.0 - a1)], [params["R2"] * (1.0 - a2)]])
        return A, B, params["R0"]

    def _ekf_step(self, x_update, p_update, current, measured_voltage, deltaT, eff, q0_as, q_noise, r_noise):
        A, B, r0 = self._state_matrices(deltaT, eff, q0_as)
        x_predict = A @ x_update + B * current
        x_predict[0, 0] = np.clip(x_predict[0, 0], 0.0, 1.0)

        soc_pred = x_predict[0, 0]
        estimated_voltage = self._ocv_from_soc(soc_pred) - x_predict[1, 0] - x_predict[2, 0] - current * r0
        p_predict = A @ p_update @ A.T + np.diag([q_noise, q_noise, q_noise])

        C = np.array([[self._docv_dsoc(soc_pred), -1.0, -1.0]])
        S = C @ p_predict @ C.T + r_noise
        K = p_predict @ C.T @ np.linalg.inv(S)

        residual = measured_voltage - estimated_voltage
        x_new = x_predict + K * residual
        x_new[0, 0] = np.clip(x_new[0, 0], 0.0, 1.0)
        p_new = (np.eye(3) - K @ C) @ p_predict
        return x_new, p_new, estimated_voltage, residual

    def download_template(self):
        path = filedialog.asksaveasfilename(initialfile="EKF_Input_Template.csv", defaultextension=".csv", filetypes=[("CSV Files", "*.csv")], title="Save CSV Template")
        if path:
            try:
                df = pd.DataFrame({"Time_s": range(0, 11), "Current_A": [2.6] * 11, "Cell_Voltage_V": [4.15 - 0.01 * i for i in range(11)]})
                df.to_csv(path, index=False)
                messagebox.showinfo("Template Downloaded", f"Successfully saved template to:\n{path}")
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

    def export_results(self):
        if self.results_df is None:
            return
        path = filedialog.asksaveasfilename(initialfile="EKF_Estimation_Results.csv", defaultextension=".csv", filetypes=[("CSV Files", "*.csv")], title="Export EKF Results")
        if path:
            try:
                self.results_df.to_csv(path, index=False)
                messagebox.showinfo("Success", "Results exported successfully!")
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to export: {exc}")

    def load_and_run(self):
        path = filedialog.askopenfilename(filetypes=[("CSV/Excel Files", "*.csv *.xlsx")], title="Load Current and Voltage Profile Data")
        if not path:
            return

        try:
            cap_ah = float(self.param_vars["Capacity (Ah)"].get())
            init_soc = self._normalize_soc(self.param_vars["Initial SOC"].get())
            eff = float(self.param_vars["Efficiency"].get())
            dt = float(self.param_vars["Sample Time (s)"].get())
            df = pd.read_csv(path) if path.endswith(".csv") else pd.read_excel(path)

            current_col = next((col for col in df.columns if "current" in col.lower() or col.strip().lower() == "i"), None)
            voltage_col = next((col for col in df.columns if "cell" in col.lower() and ("voltage" in col.lower() or col.lower().strip() == "v")), None)
            if voltage_col is None:
                voltage_col = next((col for col in df.columns if "voltage" in col.lower() or col.strip().lower() in ("v", "vl")), None)
            if not current_col:
                raise ValueError("Could not find a current column. Please name it 'Current_A' or similar.")
            if not voltage_col:
                raise ValueError("Could not find a voltage column. Please include 'Cell_Voltage_V' or similar.")

            np_cells = float(self.param_vars["Parallel Cells (Np)"].get())
            current_profile = df[current_col].to_numpy(dtype=float) / np_cells
            voltage_profile = df[voltage_col].to_numpy(dtype=float)
            if self.invert_current_var.get():
                current_profile = -current_profile

            self.run_ekf_algorithm(current_profile, voltage_profile, cap_ah, init_soc, eff, dt)
        except Exception as exc:
            messagebox.showerror("Simulation Error", f"An error occurred:\n\n{exc}")

    def run_ekf_algorithm(self, current_profile, voltage_profile, q0_ah, init_soc, eff, deltaT):
        n_samples = min(len(current_profile), len(voltage_profile))
        current_profile = current_profile[:n_samples]
        voltage_profile = voltage_profile[:n_samples]
        q0_as = q0_ah * 3600.0

        x_update = np.zeros((3, n_samples))
        x_update[:, 0] = [init_soc, 0.0, 0.0]
        voltage_est = np.zeros(n_samples)
        residuals = np.zeros(n_samples)
        voltage_est[0] = self._ocv_from_soc(init_soc) - current_profile[0] * self._ecm_params()["R0"]

        p_val = float(self.param_vars["Initial Cov. P"].get())
        p_update = np.diag([p_val, p_val, p_val])
        q_noise = float(self.param_vars["Process Noise Q"].get())
        r_noise = float(self.param_vars["Meas. Noise R"].get())

        for index in range(1, n_samples):
            x_col, p_update, voltage_est[index], residuals[index] = self._ekf_step(
                x_update[:, [index - 1]], p_update, current_profile[index], voltage_profile[index], deltaT, eff, q0_as, q_noise, r_noise
            )
            x_update[:, index] = x_col[:, 0]

        time_array = np.arange(n_samples) * deltaT
        self.results_df = pd.DataFrame(
            {
                "Time_s": time_array,
                "Current_A": current_profile,
                "Measured_Voltage_V": voltage_profile,
                "Estimated_Voltage_V": voltage_est,
                "Voltage_Residual_V": residuals,
                "EKF_SOC": x_update[0, :],
            }
        )
        self.btn_export.config(state="normal")
        self.plot_results(time_array, x_update[0, :], voltage_profile, voltage_est)

    def plot_results(self, t, soc_ekf, v_meas, v_ekf):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        ax1.plot(t, soc_ekf * 100, "b-", label="EKF Estimated SOC")
        ax1.set_ylabel("State of Charge [%]")
        ax1.set_title("SOC Estimation using Extended Kalman Filter")
        ax1.grid(True)
        ax1.legend()

        ax2.plot(t, v_meas, "g", label="Measured Terminal Voltage")
        ax2.plot(t, v_ekf, "r--", label="Estimated Terminal Voltage")
        ax2.set_xlabel("Time [s]")
        ax2.set_ylabel("Voltage [V]")
        ax2.grid(True)
        ax2.legend()
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, self.plot_frame)
        toolbar.update()

    def toggle_live_ekf(self):
        if not self.live_active:
            try:
                self.cap_ah = float(self.param_vars["Capacity (Ah)"].get())
                self.init_soc = self._normalize_soc(self.param_vars["Initial SOC"].get())
                self.eff = float(self.param_vars["Efficiency"].get())
                self.Q0 = self.cap_ah * 3600.0
                p_val = float(self.param_vars["Initial Cov. P"].get())
                self.P = np.diag([p_val, p_val, p_val])
                self.Q_noise = float(self.param_vars["Process Noise Q"].get())
                self.R_noise = float(self.param_vars["Meas. Noise R"].get())
                self._ecm_params()
            except Exception as exc:
                messagebox.showerror("EKF Settings Error", str(exc), parent=self.window)
                return

            self.live_active = True
            self.waiting_for_serial_soc = True
            self.X_update = np.array([[self.init_soc], [0.0], [0.0]])
            self.btn_live.config(text="Stop Live EKF", bg=self.colors["btn_disconnect"])
            self.lbl_live_soc.config(text="Live SOC: Waiting for serial OCV SOC...", fg=self.colors["status_ok"])

            self.start_time = None
            self.last_update_time = None
            self.acc_current = []
            self.acc_voltage = []
            self.live_data = {"t": [], "soc": [], "v_meas": [], "v_est": [], "residual": []}

            for widget in self.plot_frame.winfo_children():
                widget.destroy()
            self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
            self.ax1.set_ylabel("State of Charge [%]")
            self.ax1.set_title("Live EKF SOC Estimation")
            self.ax1.grid(True)
            self.ax2.set_xlabel("Time [s]")
            self.ax2.set_ylabel("Voltage [V]")
            self.ax2.grid(True)
            self.line_soc, = self.ax1.plot([], [], "b-", label="EKF Estimated SOC")
            self.line_v_meas, = self.ax2.plot([], [], "g-", label="Measured Terminal Voltage")
            self.line_v_est, = self.ax2.plot([], [], "r--", label="Estimated Terminal Voltage")
            self.ax1.legend(loc="upper right")
            self.ax2.legend(loc="upper right")
            self.fig.tight_layout()
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
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
            if self.live_data["t"]:
                self.results_df = pd.DataFrame(
                    {
                        "Time_s": self.live_data["t"],
                        "EKF_SOC": self.live_data["soc"],
                        "Measured_Voltage_V": self.live_data["v_meas"],
                        "Estimated_Voltage_V": self.live_data["v_est"],
                        "Voltage_Residual_V": self.live_data["residual"],
                    }
                )
                self.btn_export.config(state="normal")
                messagebox.showinfo("Live Monitoring Stopped", "The live session has finished. You can now export the recorded EKF estimations to CSV.")

    def push_live_data(self, current_A, voltage_V, timestamp, soc_ocv_percent=None):
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
            if soc_ocv_percent is not None:
                self.X_update[0, 0] = self._normalize_soc(soc_ocv_percent)
                self.waiting_for_serial_soc = False
                self.lbl_live_soc.config(text=f"Live SOC: {self.X_update[0, 0] * 100:.2f} %")
            else:
                self.lbl_live_soc.config(text=f"Live SOC: {self.init_soc * 100:.2f} % (manual init)")
            return

        target_dt = float(self.param_vars["Sample Time (s)"].get())
        self.acc_current.append(cell_current_A)
        self.acc_voltage.append(voltage_V)
        actual_dt = timestamp - self.last_update_time
        if actual_dt >= target_dt:
            self.last_update_time = timestamp
            avg_i = float(np.mean(self.acc_current))
            avg_v = float(np.mean(self.acc_voltage))
            self.acc_current = []
            self.acc_voltage = []
            self.step_live_ekf(avg_i, avg_v, actual_dt, timestamp)

    def step_live_ekf(self, i, measured_voltage, deltaT, timestamp):
        self.X_update, self.P, estimated_voltage, residual = self._ekf_step(
            self.X_update, self.P, i, measured_voltage, deltaT, self.eff, self.Q0, self.Q_noise, self.R_noise
        )
        t_elapsed = timestamp - self.start_time
        self.live_data["t"].append(t_elapsed)
        self.live_data["soc"].append(self.X_update[0, 0])
        self.live_data["v_meas"].append(measured_voltage)
        self.live_data["v_est"].append(estimated_voltage)
        self.live_data["residual"].append(residual)
        self.lbl_live_soc.config(text=f"Live SOC: {self.X_update[0, 0] * 100:.2f} %")

    def update_live_plot(self):
        if not self.live_active:
            return
        if self.live_data["t"]:
            self.line_soc.set_data(self.live_data["t"], np.array(self.live_data["soc"]) * 100)
            self.line_v_meas.set_data(self.live_data["t"], self.live_data["v_meas"])
            self.line_v_est.set_data(self.live_data["t"], self.live_data["v_est"])
            self.ax1.relim()
            self.ax1.autoscale_view()
            self.ax2.relim()
            self.ax2.autoscale_view()
            self.canvas.draw()
        self.plot_update_id = self.window.after(1000, self.update_live_plot)
