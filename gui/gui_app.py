"""
Main GUI Application - IoT Version (SINTA 2 FINAL POLISH)
Updates:
1. Attractive Header Status (Dot Indicator)
2. Re-introduced Relay Status in Side Panel
3. Perfected Layout & Fonts
"""

from core.updater import OTAUpdater  # <--- Tambahan Baru
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import time
import csv
import subprocess
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
from core import IoTClient

# --- FUNGSI BARU: PENCARI JALUR ASET ---
def resource_path(relative_path):
    """ Dapatkan path absolute ke resource, baik untuk dev maupun PyInstaller """
    try:
        # PyInstaller membuat folder temp dan menyimpannya di _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class FirmataControllerApp(tk.Tk):
    def __init__(self):
        try:
            import ctypes 
            # GANTI STRING INI (Misal jadi .fixed atau .v101)
            myappid = 'andriani.smartamp.final.release.v1.0.build2024' 
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception: pass
        
        super().__init__()
        
        self.theme = {
            "bg_root": "#0d1117", 
            "bg_header": "#161b22",
            "bg_card": "#161b22", 
            "text_primary": "#e6edf3", 
            "text_muted": "#8b949e",
            "accent_blue": "#58a6ff", 
            "accent_red": "#f85149",
            "accent_green": "#2ea043", 
            "accent_yellow": "#d29922",
            "border": "#30363d",
            "btn_active": "#238636",
            "btn_inactive": "#21262d",
            "btn_record_on": "#da3633",
            "btn_record_off": "#21262d"
        }
        
        self.title("Smart Amp IoT Protection (v1.0)")
        try: 
            icon_path = resource_path("logo.ico")
            self.iconbitmap(default=icon_path)       # Icon Window
            self.wm_iconbitmap(icon_path)    # Icon Taskbar (Paksa)
        except Exception as e:
            # Ubah pass jadi print error biar ketahuan kalau gagal
            print(f"Gagal memuat icon: {e}")
        
        self.configure(bg=self.theme["bg_root"])
        self.state("zoomed")
        self.minsize(1200, 750)
        self._setup_styles()

        self.iot = IoTClient()
        # --- INIT UPDATER ---
        self.app_version = "1.0" #pastikan ganti ini sebelu realise versi terbaru 
        self.updater = OTAUpdater(current_version=self.app_version)
        
        # --- VARIABLES ---
        self.broker_address = tk.StringVar(value="broker.emqx.io")
        self.setpoint_temp = tk.DoubleVar(value=60.0) 
        self.setpoint_curr = tk.DoubleVar(value=2.0)  
        self.cal_temp = tk.DoubleVar(value=0.0)
        self.cal_curr = tk.DoubleVar(value=0.0)

        self.txt_logic_temp = tk.StringVar(value="OVER TEMP (>60°C)")
        self.txt_logic_curr = tk.StringVar(value="SHORT CIRCUIT (>2A)")

        self.is_monitoring = False
        self.temp_data = deque([0.0]*60, maxlen=60)
        self.curr_data = deque([0.0]*60, maxlen=60)
        
        self.inputA = tk.BooleanVar(value=False) 
        self.inputB = tk.BooleanVar(value=False) 
        self.gate_type = tk.StringVar(value="OR") 
        
        self.is_recording = False
        self.csv_filename = ""
        self.record_interval = tk.IntVar(value=1)
        self.last_record_time = 0.0
        self.blink_state = False
        self.sim_short_circuit = False 

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=self.theme["bg_root"])
        style.configure("Card.TFrame", background=self.theme["bg_card"])
        style.configure("TLabel", background=self.theme["bg_card"], foreground=self.theme["text_primary"], font=("Segoe UI", 10))
        style.configure("TNotebook", background=self.theme["bg_root"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=[15, 8], font=("Segoe UI", 10, "bold"), background=self.theme["bg_header"], foreground=self.theme["text_muted"])
        style.map("TNotebook.Tab", background=[("selected", self.theme["bg_card"])], foreground=[("selected", self.theme["accent_blue"])])
        style.configure("Accent.TButton", background=self.theme["accent_blue"], foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("Accent.TButton", background=[("active", "#1f6feb")])
        style.configure("Destructive.TButton", background=self.theme["accent_red"], foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("Destructive.TButton", background=[("active", "#d03633")])
        style.configure("Switch.TCheckbutton", background=self.theme["bg_card"], foreground=self.theme["text_primary"], font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        # --- HEADER ---
        header = tk.Frame(self, bg=self.theme["bg_header"], height=60)
        header.pack(fill="x", side="top"); header.pack_propagate(False)
        
        # Left: Title
        tk.Label(header, text="🛡️ Smart Amp IoT System", font=("Segoe UI", 16, "bold"), bg=self.theme["bg_header"], fg="white").pack(side="left", padx=20)
        tk.Label(header, text="Remote Dashboard", font=("Segoe UI", 10), bg=self.theme["bg_header"], fg=self.theme["text_muted"]).pack(side="left", pady=(5,0))
        
        # Right: CLOUD STATUS (Polished)
        status_frame = tk.Frame(header, bg=self.theme["bg_header"])
        status_frame.pack(side="right", padx=20)
        
        # Container Badge
        badge = tk.Frame(status_frame, bg="#21262d", padx=10, pady=5, highlightthickness=1, highlightbackground=self.theme["border"])
        badge.pack(side="right")
        
        tk.Label(badge, text="CLOUD CONNECTION:", font=("Segoe UI", 8, "bold"), bg="#21262d", fg="#8b949e").pack(side="left", padx=(0,8))
        
        # Dot Indicator
        self.cloud_dot = tk.Canvas(badge, width=10, height=10, bg="#21262d", highlightthickness=0)
        self.cloud_dot.pack(side="left")
        self.cloud_dot_id = self.cloud_dot.create_oval(1,1,9,9, fill="#30363d", outline="") # Default Grey
        
        # Text Status
        self.lbl_cloud_text = tk.Label(badge, text="OFFLINE", font=("Segoe UI", 9, "bold"), bg="#21262d", fg="#8b949e")
        self.lbl_cloud_text.pack(side="left", padx=(5,0))

        # --- MAIN LAYOUT ---
        main_container = tk.Frame(self, bg=self.theme["bg_root"])
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=0, minsize=250) 
        main_container.grid_columnconfigure(1, weight=5)              
        main_container.grid_columnconfigure(2, weight=0, minsize=320) 
        main_container.grid_rowconfigure(0, weight=1)

        # LEFT
        left_panel = tk.Frame(main_container, bg=self.theme["bg_root"])
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        self._build_connection_card(left_panel)
        self._build_control_card(left_panel) 
        self._build_simulation_card(left_panel)

        # MIDDLE
        middle_panel = tk.Frame(main_container, bg=self.theme["bg_root"])
        middle_panel.grid(row=0, column=1, sticky="nsew")
        self.notebook = ttk.Notebook(middle_panel)
        self.notebook.pack(fill="both", expand=True)
        self.tab_monitor = ttk.Frame(self.notebook, style="Card.TFrame")
        self.notebook.add(self.tab_monitor, text="   📊 Live Monitor   ")
        self._build_monitor_tab(self.tab_monitor)
        self.tab_logic = ttk.Frame(self.notebook, style="Card.TFrame")
        self.notebook.add(self.tab_logic, text="   ⚡ Logic Analysis   ")
        self._build_logic_tab(self.tab_logic) 

        # RIGHT
        right_panel = tk.Frame(main_container, bg=self.theme["bg_root"])
        right_panel.grid(row=0, column=2, sticky="nsew", padx=(8,0))
        self._build_stats_card(right_panel)
        self._build_logger_card(right_panel)
        
        self.status_bar = tk.Label(self, text="Waiting for Connection...", bg=self.theme["bg_header"], fg=self.theme["text_muted"], anchor="w", padx=10)
        self.status_bar.pack(fill="x", side="bottom", pady=(5,0))

    def _create_card_frame(self, parent, title, expand_content=False):
        frame = tk.Frame(parent, bg=self.theme["bg_card"], highlightthickness=1, highlightbackground=self.theme["border"])
        if expand_content: frame.pack(fill="both", expand=True, pady=(0, 10))
        else: frame.pack(fill="x", pady=(0, 10))
        header = tk.Frame(frame, bg=self.theme["bg_card"])
        header.pack(fill="x", padx=12, pady=8)
        tk.Label(header, text=title, font=("Segoe UI", 10, "bold"), bg=self.theme["bg_card"], fg="white").pack(side="left")
        tk.Frame(frame, bg=self.theme["border"], height=1).pack(fill="x")
        content = tk.Frame(frame, bg=self.theme["bg_card"], padx=12, pady=12)
        content.pack(fill="both", expand=True)
        return content

    def _build_connection_card(self, parent):
        content = self._create_card_frame(parent, "MQTT Connection")
        tk.Label(content, text="Broker Address:", bg=self.theme["bg_card"], fg="grey").pack(anchor="w")
        self.ent_broker = ttk.Entry(content, textvariable=self.broker_address)
        self.ent_broker.pack(fill="x", pady=(5, 10))
        self.btn_connect = ttk.Button(content, text="Connect Cloud", style="Accent.TButton", command=self.toggle_connection)
        self.btn_connect.pack(fill="x")

    def _build_control_card(self, parent):
        content = self._create_card_frame(parent, "System Configuration")
        
        # LIMITS
        tk.Label(content, text="⚠️ SAFETY THRESHOLDS", font=("Segoe UI", 8, "bold"), bg=self.theme["bg_card"], fg="#8b949e").pack(anchor="w", pady=(0,8))
        
        row_t = tk.Frame(content, bg=self.theme["bg_card"]); row_t.pack(fill="x", pady=2)
        tk.Label(row_t, text="Max Temp (°C)", fg=self.theme["accent_blue"], bg=self.theme["bg_card"], font=("Segoe UI", 9)).pack(side="left")
        tk.Spinbox(row_t, from_=40, to=100, increment=1, textvariable=self.setpoint_temp, width=6, 
                   bg="#0d1117", fg="white", bd=0, buttonbackground=self.theme["border"]).pack(side="right")

        row_c = tk.Frame(content, bg=self.theme["bg_card"]); row_c.pack(fill="x", pady=2)
        tk.Label(row_c, text="Max Current (A)", fg=self.theme["accent_yellow"], bg=self.theme["bg_card"], font=("Segoe UI", 9)).pack(side="left")
        tk.Spinbox(row_c, from_=0.1, to=10.0, increment=0.1, textvariable=self.setpoint_curr, width=6, 
                   bg="#0d1117", fg="white", bd=0, buttonbackground=self.theme["border"]).pack(side="right")

        tk.Frame(content, bg=self.theme["border"], height=1).pack(fill="x", pady=10)

        # CALIBRATION
        tk.Label(content, text="🔧 SENSOR CALIBRATION", font=("Segoe UI", 8, "bold"), bg=self.theme["bg_card"], fg="#8b949e").pack(anchor="w", pady=(0,8))
        
        row_cal_t = tk.Frame(content, bg=self.theme["bg_card"]); row_cal_t.pack(fill="x", pady=2)
        tk.Label(row_cal_t, text="Temp Offset (±)", fg="#8b949e", bg=self.theme["bg_card"], font=("Segoe UI", 9)).pack(side="left")
        tk.Spinbox(row_cal_t, from_=-10.0, to=10.0, increment=0.5, textvariable=self.cal_temp, width=6, 
                   bg="#0d1117", fg="white", bd=0, buttonbackground=self.theme["border"]).pack(side="right")
        
        row_cal_c = tk.Frame(content, bg=self.theme["bg_card"]); row_cal_c.pack(fill="x", pady=2)
        tk.Label(row_cal_c, text="Curr Offset (±)", fg="#8b949e", bg=self.theme["bg_card"], font=("Segoe UI", 9)).pack(side="left")
        tk.Spinbox(row_cal_c, from_=-2.0, to=2.0, increment=0.01, textvariable=self.cal_curr, width=6, 
                   bg="#0d1117", fg="white", bd=0, buttonbackground=self.theme["border"]).pack(side="right")

        tk.Frame(content, bg=self.theme["border"], height=1).pack(fill="x", pady=10)

        # REMOTE COMMAND
        cmd_frame = tk.Frame(content, bg="#0d1117", padx=8, pady=8, highlightthickness=1, highlightbackground=self.theme["border"])
        cmd_frame.pack(fill="x")
        tk.Label(cmd_frame, text="⚡ REMOTE OVERRIDE", font=("Segoe UI", 8, "bold"), bg="#0d1117", fg="#8b949e").pack(pady=(0,5))
        
        btn_row = tk.Frame(cmd_frame, bg="#0d1117"); btn_row.pack(fill="x")
        self.btn_on = tk.Button(btn_row, text="ACTIVATE", font=("Segoe UI", 8, "bold"), bg=self.theme["btn_inactive"], fg="#2ea043", 
                               bd=0, cursor="hand2", command=lambda: self.iot.send_command("ON"))
        self.btn_on.pack(side="left", fill="x", expand=True, padx=(0,2), ipady=5)
        
        self.btn_off = tk.Button(btn_row, text="SHUTDOWN", font=("Segoe UI", 8, "bold"), bg=self.theme["accent_red"], fg="white", 
                                bd=0, cursor="hand2", command=lambda: self.iot.send_command("OFF"))
        self.btn_off.pack(side="right", fill="x", expand=True, padx=(2,0), ipady=5)

    def _build_simulation_card(self, parent):
        content = self._create_card_frame(parent, "⚠️ Simulation")
        def toggle_short():
            self.sim_short_circuit = not self.sim_short_circuit
            if self.sim_short_circuit:
                self.btn_sim.config(text="STOP SIMULATION", bg=self.theme["accent_red"])
            else:
                self.btn_sim.config(text="TEST SHORT CIRCUIT", bg=self.theme["btn_inactive"])
        
        self.btn_sim = tk.Button(content, text="TEST SHORT CIRCUIT", bg=self.theme["btn_inactive"], fg="white", 
                                font=("Segoe UI", 9, "bold"), bd=0, command=toggle_short)
        self.btn_sim.pack(fill="x", ipady=5)
        tk.Label(content, text="*Note: Manual Reset Required (Safety Latch)", bg=self.theme["bg_card"], fg="grey", font=("Segoe UI", 7, "italic")).pack(pady=(5,0))

    def _build_monitor_tab(self, parent):
        container = tk.Frame(parent, bg=self.theme["bg_card"])
        container.pack(fill="both", expand=True, padx=15, pady=15)
        
        top_frame = tk.Frame(container, bg=self.theme["bg_card"])
        top_frame.pack(fill="x", pady=(0, 15))
        top_frame.grid_columnconfigure(0, weight=1); top_frame.grid_columnconfigure(1, weight=1)
        
        # Power Box
        power_box = tk.Frame(top_frame, bg="#21262d", highlightthickness=1, highlightbackground=self.theme["border"], height=160)
        power_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10)); power_box.pack_propagate(False)
        p_in = tk.Frame(power_box, bg="#21262d"); p_in.pack(fill="both", expand=True, padx=15, pady=15)
        tk.Label(p_in, text="POWER LOAD (INA219)", font=("Segoe UI", 10, "bold"), bg="#21262d", fg="grey").pack(anchor="w")
        p_val_frame = tk.Frame(p_in, bg="#21262d"); p_val_frame.pack(expand=True)
        
        self.lbl_volt = tk.Label(p_val_frame, text="0.0 V", font=("Segoe UI", 18, "bold"), bg="#21262d", fg=self.theme["accent_yellow"])
        self.lbl_volt.pack(side="left", padx=5)
        tk.Label(p_val_frame, text="|", font=("Segoe UI", 20), bg="#21262d", fg="#30363d").pack(side="left", padx=5)
        self.lbl_curr = tk.Label(p_val_frame, text="0.00 A", font=("Segoe UI", 26, "bold"), bg="#21262d", fg="white")
        self.lbl_curr.pack(side="left", padx=5)

        # Temp Box
        temp_box = tk.Frame(top_frame, bg="#21262d", highlightthickness=1, highlightbackground=self.theme["border"], height=160)
        temp_box.grid(row=0, column=1, sticky="nsew"); temp_box.pack_propagate(False)
        t_in = tk.Frame(temp_box, bg="#21262d"); t_in.pack(fill="both", expand=True, padx=20, pady=15)
        h_t = tk.Frame(t_in, bg="#21262d"); h_t.pack(fill="x")
        tk.Label(h_t, text="DEVICE TEMP (LM35)", font=("Segoe UI", 10, "bold"), bg="#21262d", fg="grey").pack(side="left")
        self.rec_dot = tk.Canvas(h_t, width=14, height=14, bg="#21262d", highlightthickness=0)
        self.rec_dot.pack(side="right")
        self.dot_id = self.rec_dot.create_oval(2,2,12,12, fill="#21262d", outline="")
        self.lbl_temp_big = tk.Label(t_in, text="0.0°C", font=("Segoe UI", 48, "bold"), bg="#21262d", fg=self.theme["accent_blue"])
        self.lbl_temp_big.pack(expand=True)

        # Graph
        graph_frame = tk.Frame(container, bg=self.theme["bg_card"]); graph_frame.pack(fill="both", expand=True)
        self.fig = Figure(figsize=(5, 3), dpi=100, facecolor=self.theme["bg_card"])
        self.fig.subplots_adjust(left=0.1, bottom=0.15, right=0.9, top=0.9)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#0d1117")
        self.ax.tick_params(axis='y', colors=self.theme["accent_blue"], labelsize=8) 
        self.ax.tick_params(axis='x', colors=self.theme["text_muted"], labelsize=8)
        self.ax.grid(True, color=self.theme["border"], linestyle='--', linewidth=0.5)
        self.ax2 = self.ax.twinx()
        self.ax2.tick_params(axis='y', colors=self.theme["accent_yellow"], labelsize=8) 
        self.line_temp, = self.ax.plot([], [], color=self.theme["accent_blue"], linewidth=2, label="Temp (°C)")
        self.line_curr, = self.ax2.plot([], [], color=self.theme["accent_yellow"], linewidth=2, label="Current (A)")
        lines = [self.line_temp, self.line_curr]
        labels = [l.get_label() for l in lines]
        self.ax.legend(lines, labels, loc='upper left', frameon=False, labelcolor='white', fontsize=8)
        self.canvas_chart = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas_chart.draw(); self.canvas_chart.get_tk_widget().pack(fill="both", expand=True)

    def _build_logic_tab(self, parent):
        container = tk.Frame(parent, bg=self.theme["bg_card"])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        gate_frame = tk.Frame(container, bg=self.theme["bg_card"]); gate_frame.pack(fill="x", pady=(0,10))
        tk.Label(gate_frame, text="LOGIC MODE:", bg=self.theme["bg_card"], fg="grey", font=("bold")).pack(anchor="w", pady=(0,5))
        gates = ["OR", "AND", "XOR"] 
        for g in gates:
            tk.Radiobutton(gate_frame, text=g, variable=self.gate_type, value=g, command=self.update_logic_visualization,
                          bg=self.theme["bg_card"], fg="white", selectcolor=self.theme["accent_blue"],
                          indicatoron=0, width=8, pady=5, bd=0).pack(side="left", padx=2)
        self.logic_canvas = tk.Canvas(container, bg="#0d1117", highlightthickness=0)
        self.logic_canvas.pack(fill="both", expand=True)
        input_frame = tk.Frame(container, bg=self.theme["bg_card"], pady=10)
        input_frame.pack(fill="x")
        f_a = tk.Frame(input_frame, bg=self.theme["bg_card"]); f_a.pack(side="left", expand=True)
        tk.Label(f_a, textvariable=self.txt_logic_temp, fg=self.theme["accent_blue"], bg=self.theme["bg_card"], font=("bold")).pack()
        ttk.Checkbutton(f_a, variable=self.inputA, style="Switch.TCheckbutton", state="disabled").pack()
        f_b = tk.Frame(input_frame, bg=self.theme["bg_card"]); f_b.pack(side="left", expand=True)
        tk.Label(f_b, textvariable=self.txt_logic_curr, fg=self.theme["accent_yellow"], bg=self.theme["bg_card"], font=("bold")).pack()
        ttk.Checkbutton(f_b, variable=self.inputB, style="Switch.TCheckbutton", state="disabled").pack()

    def _build_stats_card(self, parent):
        content = self._create_card_frame(parent, "Live Statistics")
        tk.Label(content, text="TEMPERATURE", font=("Segoe UI", 8, "bold"), bg=self.theme["bg_card"], fg=self.theme["accent_blue"]).pack(anchor="w")
        self.stat_temp_max = self._add_stat(content, "Max:", "0.0°C")
        self.stat_temp_min = self._add_stat(content, "Min:", "0.0°C")
        self.stat_temp_avg = self._add_stat(content, "Avg:", "0.0°C")
        
        tk.Frame(content, bg=self.theme["border"], height=1).pack(fill="x", pady=8)
        
        tk.Label(content, text="CURRENT (AMPERE)", font=("Segoe UI", 8, "bold"), bg=self.theme["bg_card"], fg=self.theme["accent_yellow"]).pack(anchor="w")
        self.stat_curr_max = self._add_stat(content, "Max:", "0.00 A")
        self.stat_curr_min = self._add_stat(content, "Min:", "0.00 A")
        self.stat_curr_avg = self._add_stat(content, "Avg:", "0.00 A")
        
        # --- KEMBALIKAN STATUS RELAY (HARDWARE) ---
        tk.Frame(content, bg=self.theme["border"], height=1).pack(fill="x", pady=8)
        
        tk.Label(content, text="PHYSICAL RELAY STATE", font=("Segoe UI", 8, "bold"), bg=self.theme["bg_card"], fg="#8b949e").pack(anchor="w")
        self.lbl_relay_status = tk.Label(content, text="UNKNOWN", font=("Segoe UI", 12, "bold"), bg=self.theme["bg_card"], fg="grey")
        self.lbl_relay_status.pack(anchor="w", pady=(2,0))
        # ------------------------------------------

    def _build_logger_card(self, parent):
        content = self._create_card_frame(parent, "Data Logger & System")
        
        # --- LOGGER SECTION ---
        int_row = tk.Frame(content, bg=self.theme["bg_card"]); int_row.pack(fill="x", pady=(0, 10))
        tk.Label(int_row, text="Log Interval (sec):", bg=self.theme["bg_card"], fg="grey").pack(side="left")
        intervals = [("1s", 1), ("5s", 5), ("10s", 10), ("30s", 30), ("60s", 60)]
        cbox = ttk.Combobox(int_row, textvariable=self.record_interval, values=[x[1] for x in intervals], width=5, state="readonly")
        cbox.pack(side="right"); cbox.current(0)
        
        self.btn_record = tk.Button(content, text="START RECORDING", font=("Segoe UI", 10, "bold"),
                                  bg=self.theme["btn_record_off"], fg="white",
                                  activebackground="#30363d", activeforeground="white",
                                  bd=0, cursor="hand2", command=self.toggle_recording)
        self.btn_record.pack(fill="x", ipady=5, pady=(0, 5))
        
        ttk.Button(content, text="Open Data Folder", command=self.open_folder).pack(fill="x")

        # Garis Pembatas
        tk.Frame(content, bg=self.theme["border"], height=1).pack(fill="x", pady=15)

        # --- OTA UPDATE SECTION (NOVELTY) ---
        v_frame = tk.Frame(content, bg=self.theme["bg_card"])
        v_frame.pack(fill="x", pady=(0,5))
        tk.Label(v_frame, text="FIRMWARE VERSION:", font=("Segoe UI", 7, "bold"), bg=self.theme["bg_card"], fg="#8b949e").pack(side="left")
        tk.Label(v_frame, text=f"v{self.app_version}", font=("Segoe UI", 7, "bold"), bg=self.theme["bg_card"], fg=self.theme["accent_blue"]).pack(side="right")
        
        self.btn_update = tk.Button(content, text="CHECK FOR UPDATES", font=("Segoe UI", 9, "bold"),
                                   bg=self.theme["btn_inactive"], fg=self.theme["accent_blue"],
                                   bd=0, cursor="hand2", command=self.check_software_update)
        self.btn_update.pack(fill="x", ipady=5)

    # --- LOGIC UPDATE ---
    def check_software_update(self):
        self.btn_update.config(text="CONNECTING TO CLOUD...", state="disabled", fg="grey")
        self.update() # Refresh UI biar gak freeze
        
        # Delay dikit biar kerasa "Loading"-nya (Simulasi proses)
        self.after(500, self._perform_update_check)

    def _perform_update_check(self):
        is_available, new_ver = self.updater.check_for_updates()
        
        self.btn_update.config(state="normal")
        
        if is_available:
            self.btn_update.config(text=f"UPDATE AVAILABLE (v{new_ver})", bg=self.theme["accent_green"], fg="white")
            ans = messagebox.askyesno("Firmware Update", f"New version v{new_ver} found on Cloud Server!\n\nCurrent Version: v{self.app_version}\nNew Version: v{new_ver}\n\nDownload and install now?")
            if ans:
                self.updater.open_download_page()
        elif new_ver == "Connection Error":
             self.btn_update.config(text="SERVER UNREACHABLE", bg=self.theme["accent_red"], fg="white")
             messagebox.showerror("Update Failed", "Cannot connect to Update Server.\nCheck internet connection.")
             self.after(2000, lambda: self.btn_update.config(text="CHECK FOR UPDATES", bg=self.theme["btn_inactive"], fg=self.theme["accent_blue"]))
        else:
            self.btn_update.config(text="SYSTEM IS UP-TO-DATE", fg=self.theme["accent_green"])
            messagebox.showinfo("System Info", f"You are using the latest version (v{self.app_version}).")
            self.after(2000, lambda: self.btn_update.config(text="CHECK FOR UPDATES", bg=self.theme["btn_inactive"], fg=self.theme["accent_blue"]))
            
    def _add_stat(self, parent, label, val):
        f = tk.Frame(parent, bg=self.theme["bg_card"]); f.pack(fill="x", pady=1)
        tk.Label(f, text=label, bg=self.theme["bg_card"], fg="grey").pack(side="left")
        v = tk.Label(f, text=val, bg=self.theme["bg_card"], fg="white", font=("bold"))
        v.pack(side="right")
        return v

    def toggle_connection(self):
        if not self.iot.is_connected:
            broker = self.broker_address.get()
            if self.iot.connect_broker(broker):
                self.btn_connect.configure(text="Disconnect Cloud", style="Destructive.TButton")
                self.status_bar.configure(text=f"Connected to {broker}", fg=self.theme["accent_green"])
                # HEADER UPDATE (ONLINE)
                self.cloud_dot.itemconfig(self.cloud_dot_id, fill=self.theme["accent_green"])
                self.lbl_cloud_text.config(text="ONLINE", fg=self.theme["accent_green"])
                
                self.is_monitoring = True
                self.update_loop()
            else:
                messagebox.showerror("Error", "Gagal connect ke Broker MQTT")
        else:
            self.iot.disconnect_broker()
            self.btn_connect.configure(text="Connect Cloud", style="Accent.TButton")
            self.is_monitoring = False
            self.status_bar.configure(text="Disconnected", fg=self.theme["text_muted"])
            # HEADER UPDATE (OFFLINE)
            self.cloud_dot.itemconfig(self.cloud_dot_id, fill="#30363d")
            self.lbl_cloud_text.config(text="OFFLINE", fg="#8b949e")
            # RELAY UPDATE (UNKNOWN)
            self.lbl_relay_status.config(text="UNKNOWN", fg="grey")

    def update_loop(self):
        if not self.is_monitoring: return
        
        data = self.iot.get_data()
        is_online = self.iot.check_online_status()
        
        # Header Status Check (Double Check)
        if is_online:
            self.cloud_dot.itemconfig(self.cloud_dot_id, fill=self.theme["accent_green"])
            self.lbl_cloud_text.config(text="ONLINE", fg=self.theme["accent_green"])
        else:
            self.cloud_dot.itemconfig(self.cloud_dot_id, fill=self.theme["accent_red"])
            self.lbl_cloud_text.config(text="DISCONNECTED", fg=self.theme["accent_red"])

        real_temp = data.get('temp', 0.0)
        real_volt = data.get('volt', 0.0)
        real_curr = data.get('curr', 0.0)
        relay_on = data.get('relay', True)
        
        calibrated_temp = real_temp + self.cal_temp.get()
        calibrated_curr = real_curr + self.cal_curr.get()
        if calibrated_curr < 0: calibrated_curr = 0.0
        
        try:
            current_limit_t = self.setpoint_temp.get()
            current_limit_c = self.setpoint_curr.get()
            self.txt_logic_temp.set(f"OVER TEMP (>{current_limit_t}°C)")
            self.txt_logic_curr.set(f"SHORT CIRCUIT (>{current_limit_c}A)")
        except:
            current_limit_t = 60.0; current_limit_c = 2.0

        if self.sim_short_circuit:
            display_curr = current_limit_c + 1.5 
        else:
            display_curr = calibrated_curr
        
        display_volt = real_volt
        display_temp = calibrated_temp
            
        self.temp_data.append(display_temp)
        self.curr_data.append(display_curr)
        
        self.lbl_temp_big.config(text=f"{display_temp:.1f}°C")
        self.lbl_volt.config(text=f"{display_volt:.2f} V")
        self.lbl_curr.config(text=f"{display_curr:.3f} A", fg=self.theme["accent_red"] if display_curr > current_limit_c else "white")
        
        t_list = list(self.temp_data); c_list = list(self.curr_data)
        if t_list:
            self.stat_temp_max.config(text=f"{max(t_list):.1f}°C")
            self.stat_temp_min.config(text=f"{min(t_list):.1f}°C")
            self.stat_temp_avg.config(text=f"{sum(t_list)/len(t_list):.1f}°C")
        if c_list:
            self.stat_curr_max.config(text=f"{max(c_list):.2f} A")
            self.stat_curr_min.config(text=f"{min(c_list):.2f} A")
            self.stat_curr_avg.config(text=f"{sum(c_list)/len(c_list):.2f} A")
        
        # --- UPDATE STATUS RELAY & BUTTONS ---
        if is_online:
            if relay_on:
                self.btn_on.config(bg=self.theme["btn_active"])
                self.btn_off.config(bg=self.theme["accent_red"])
                # Update Label di Panel Kanan
                self.lbl_relay_status.config(text="ACTIVE (ON)", fg=self.theme["accent_green"])
            else:
                self.btn_on.config(bg=self.theme["btn_inactive"])
                self.btn_off.config(bg="#800000")
                # Update Label di Panel Kanan
                self.lbl_relay_status.config(text="CUT OFF (PROTECTED)", fg=self.theme["accent_red"])
        else:
            self.lbl_relay_status.config(text="UNKNOWN", fg="grey")

        self.line_temp.set_data(range(len(self.temp_data)), self.temp_data)
        self.line_curr.set_data(range(len(self.curr_data)), self.curr_data)
        
        if len(self.temp_data) > 0:
            self.ax.set_ylim(min(self.temp_data)-5, max(self.temp_data)+10)
            self.ax2.set_ylim(0, max(self.curr_data)*1.5 + 0.5)
        
        self.ax.set_xlim(0, 60)
        self.canvas_chart.draw_idle()

        is_over_temp = display_temp > current_limit_t
        is_short_circuit = display_curr > current_limit_c
        
        self.inputA.set(is_over_temp)
        self.inputB.set(is_short_circuit)
        
        gate = self.gate_type.get()
        protect_trigger = False
        if gate == "OR": protect_trigger = is_over_temp or is_short_circuit
        elif gate == "AND": protect_trigger = is_over_temp and is_short_circuit
        elif gate == "XOR": protect_trigger = is_over_temp != is_short_circuit
        
        self.draw_logic_circuit(is_over_temp, is_short_circuit, protect_trigger, gate)
        
        if protect_trigger and relay_on and is_online:
            print("Logic Triggered -> Sending Force OFF")
            self.iot.send_command("OFF")
        
        if self.is_recording:
            self.write_csv(display_temp, display_volt, display_curr, protect_trigger)

        self.after(200, self.update_loop)

    def toggle_recording(self):
        if not self.is_recording:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.csv_filename = f"DataLog_{ts}.csv"
            with open(self.csv_filename, 'w', newline='') as f:
                csv.writer(f).writerow(["Time", "Temp(C)", "Volt(V)", "Curr(A)", "Protection_Active"])
            self.is_recording = True
            self.btn_record.config(text="STOP RECORDING", bg=self.theme["btn_record_on"])
            self._animate_rec_dot()
        else:
            self.is_recording = False
            self.btn_record.config(text="START RECORDING", bg=self.theme["btn_record_off"])
            self.rec_dot.itemconfig(self.dot_id, fill="#21262d")

    def _animate_rec_dot(self):
        if not self.is_recording: return
        col = "#da3633" if not self.blink_state else "#21262d"
        self.rec_dot.itemconfig(self.dot_id, fill=col)
        self.blink_state = not self.blink_state
        self.after(500, self._animate_rec_dot)

    def write_csv(self, t, v, i, prot):
        if time.time() - self.last_record_time < self.record_interval.get(): return
        self.last_record_time = time.time()
        with open(self.csv_filename, 'a', newline='') as f:
            csv.writer(f).writerow([datetime.now().strftime("%H:%M:%S"), t, f"{v:.2f}", f"{i:.2f}", prot])

    def open_folder(self):
        path = os.getcwd()
        if os.name == 'nt': os.startfile(path)
        else: subprocess.Popen(["xdg-open", path])

    def draw_logic_circuit(self, a, b, out, gate):
        c = self.logic_canvas; c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w<10: return
        cx, cy = w//2, h//2
        col_a = self.theme["accent_red"] if a else "#30363d" 
        col_b = self.theme["accent_red"] if b else "#30363d" 
        col_out = self.theme["accent_red"] if out else self.theme["accent_green"] 
        outline_col = "white"
        c.create_line(40, cy-30, cx-40, cy-30, fill=col_a, width=3)
        c.create_line(40, cy+30, cx-40, cy+30, fill=col_b, width=3)
        c.create_line(cx+30, cy, w-40, cy, fill=col_out, width=3)
        if gate == "AND":
            c.create_line(cx-40, cy-40, cx-40, cy+40, fill=outline_col, width=2)
            c.create_line(cx-40, cy-40, cx-10, cy-40, fill=outline_col, width=2)
            c.create_line(cx-40, cy+40, cx-10, cy+40, fill=outline_col, width=2)
            c.create_arc(cx-50, cy-40, cx+30, cy+40, start=-90, extent=180, style="arc", outline=outline_col, width=2)
            eq_text = "Q = A • B"
        elif gate == "OR":
            c.create_arc(cx-80, cy-40, cx-20, cy+40, start=-70, extent=140, style="arc", outline=outline_col, width=2)
            c.create_arc(cx-90, cy-50, cx+50, cy+50, start=0, extent=100, style="arc", outline=outline_col, width=2)
            c.create_arc(cx-90, cy-50, cx+50, cy+50, start=-100, extent=100, style="arc", outline=outline_col, width=2)
            eq_text = "Q = A + B"
        elif gate == "XOR":
            c.create_arc(cx-90, cy-40, cx-30, cy+40, start=-70, extent=140, style="arc", outline=outline_col, width=2)
            c.create_arc(cx-80, cy-40, cx-20, cy+40, start=-70, extent=140, style="arc", outline=outline_col, width=2)
            c.create_arc(cx-90, cy-50, cx+50, cy+50, start=0, extent=100, style="arc", outline=outline_col, width=2)
            c.create_arc(cx-90, cy-50, cx+50, cy+50, start=-100, extent=100, style="arc", outline=outline_col, width=2)
            eq_text = "Q = A ⊕ B"
        status_text = "TRIGGERED" if out else "SAFE"
        c.create_text(cx, h-40, text=f"STATUS: {status_text}", fill=col_out, font=("Segoe UI", 10, "bold"))
        c.create_text(cx, h-20, text=eq_text, fill="white", font=("Segoe UI", 14, "italic"))

    def update_logic_visualization(self, *args): self.update()
    def on_close(self):
        self.iot.disconnect_broker()
        self.destroy()

if __name__ == "__main__":
    app = FirmataControllerApp()
    app.mainloop()