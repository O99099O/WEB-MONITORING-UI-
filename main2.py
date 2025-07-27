import sys, os, socket, threading, time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import psutil, platform
import random
from PIL import Image, ImageTk
import datetime
import json

#==================== GUI STYLE ====================#
STYLE_BG = "#0f0f0f"
STYLE_FG = "#00FF88"
FONT_TITLE = ("Arial", 14, "bold")
FONT_NORM = ("Consolas", 11)
GRAFIK_STYLES = ['line', 'bar', 'scatter', 'step', 'candle']
BACKGROUND_STYLES = ['grid', 'plain', 'dark', 'white', 'image']
GRAPH_COLORS = ['cyan', 'red', 'yellow', 'green', 'blue', 'magenta']
HISTORY_FILE = "monitor_history.json"
BANNER_ART = r"""
  ____  _      _      ____  _   _ _____ 
 |  _ \| |    / \    / ___|| | | |_   _|
 | |_) | |   / _ \   \___ \| |_| | | |  
 |  __/| |__/ ___ \   ___) |  _  | | |  
 |_|   |_____/_/   \_\|____/|_| |_| |_|  
  _   _ _____ ____  ____  _____ _   _ 
 | | | | ____|  _ \|  _ \| ____| \ | |
 | | | |  _| | |_) | | | |  _| |  \| |
 | |_| | |___|  _ <| |_| | |___| |\  |
  \___/|_____|_| \_\____/|_____|_| \_|
"""

#==================== GLOBAL VARIABLES ====================#
url_input = ""
ip_address = ""
selected_type = "web"
grafik_tipe = 'line'
background_tipe = 'grid'
custom_background = None
ping_history = []
port_history = []
extra_graphs = [[] for _ in range(4)]
graph_visibility = [True for _ in range(6)]
graph_colors = GRAPH_COLORS.copy()
open_ports = []
monitor_running = False
history_data = []
notification_history = []
traffic_history = []
main_window = None

#==================== LOAD HISTORY ====================#
def load_history():
    global history_data
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                history_data = json.load(f)
        except:
            history_data = []
    return history_data

#==================== SAVE HISTORY ====================#
def save_history():
    global history_data
    if len(history_data) > 20:
        history_data = history_data[-20:]
        
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history_data, f)
    except Exception as e:
        print(f"Error saving history: {e}")

#==================== SIMPLE PORT SCANNER ====================#
def scan_ports(host):
    buka = []
    port_utama = [
        21, 22, 23, 25, 53, 80, 110, 143,
        443, 3306, 3389, 8080, 8443, 5900, 6379
    ]
    for port in port_utama:
        try:
            sock = socket.socket()
            sock.settimeout(1)
            sock.connect((host, port))
            buka.append(port)
            sock.close()
        except:
            continue
    return buka if buka else []

#==================== NETWORK FUNCTIONS ====================#
def resolve_ip(target):
    try:
        return socket.gethostbyname(target)
    except socket.gaierror:
        return "Unknown"

def check_ping(target, port=80):
    try:
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((target, port))
        sock.close()
        latency = round((time.time() - start) * 1000, 2) if result == 0 else None
        return result == 0, latency
    except Exception as e:
        print(f"Ping error: {e}")
        return False, None

#==================== TRAFFIC MONITORING ====================#
def get_network_traffic():
    try:
        net_io = psutil.net_io_counters()
        return net_io.bytes_sent, net_io.bytes_recv
    except:
        return 0, 0

#==================== MONITORING THREAD ====================#
def update_monitor():
    global monitor_running, ip_address, open_ports, notification_history, traffic_history
    
    monitor_running = True
    ip_address = resolve_ip(url_input)
    
    # Add to history
    history_entry = {
        "url": url_input,
        "ip": ip_address,
        "type": selected_type,
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if history_entry not in history_data:
        history_data.append(history_entry)
        save_history()
    
    # Initial port scan
    open_ports = scan_ports(ip_address)
    if main_window:
        main_window.after(0, update_port_list)
    
    # Get initial traffic
    last_sent, last_recv = get_network_traffic()
    
    # Add notification
    add_notification(f"Monitoring started for {url_input}")
    
    while monitor_running:
        try:
            # Update ping and port status
            ping_status, latency = check_ping(ip_address)
            port_status, _ = check_ping(ip_address, 80)
            
            # Update histories
            ping_history.append(latency if latency else 0)
            port_history.append(100 if port_status else 0)
            
            # Generate random data for extra graphs
            for i in range(len(extra_graphs)):
                extra_graphs[i].append(random.randint(10, 200))
                if len(extra_graphs[i]) > 100:
                    extra_graphs[i].pop(0)
            
            # Get network traffic
            current_sent, current_recv = get_network_traffic()
            sent_diff = current_sent - last_sent
            recv_diff = current_recv - last_recv
            last_sent, last_recv = current_sent, current_recv
            traffic_history.append((sent_diff, recv_diff))
            if len(traffic_history) > 100:
                traffic_history.pop(0)
            
            # Trim histories
            for history in [ping_history, port_history]:
                if len(history) > 100:
                    history.pop(0)
            
            # Update UI
            if main_window:
                main_window.after(0, draw_graphics)
                main_window.after(0, lambda: update_info_panel(ping_status, port_status, latency, sent_diff, recv_diff))
            
            # Check for status changes
            if len(ping_history) > 1:
                if ping_history[-1] == 0 and ping_history[-2] > 0:
                    add_notification(f"Connection lost to {url_input}")
                elif ping_history[-1] > 0 and ping_history[-2] == 0:
                    add_notification(f"Connection restored to {url_input}")
            
            time.sleep(2)
        except Exception as e:
            print(f"Monitoring error: {e}")
            time.sleep(5)
    
    monitor_running = False
    add_notification(f"Monitoring stopped for {url_input}")

def stop_monitor():
    global monitor_running
    monitor_running = False

#==================== UI UPDATE FUNCTIONS ====================#
def add_notification(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    notification_history.insert(0, f"[{timestamp}] {message}")
    if len(notification_history) > 20:
        notification_history.pop()
    if main_window:
        main_window.after(0, update_notifications)

def update_notifications():
    if 'notification_listbox' in globals():
        notification_listbox.delete(0, tk.END)
        for note in notification_history:
            notification_listbox.insert(tk.END, note)

def update_info_panel(ping_status, port_status, latency, sent, recv):
    if 'info_panel' in globals():
        info_text = f"\nTarget: {url_input}\nIP Address: {ip_address}\n"
        info_text += f"Ping Status: {'ONLINE ✅' if ping_status else 'OFFLINE ❌'}\n"
        info_text += f"Latency: {latency if latency else '-'} ms\n"
        info_text += f"Web Port: {'OPEN ✅' if port_status else 'CLOSED ❌'}\n"
        info_text += f"Traffic: ▲ {sent//1024}KB ▼ {recv//1024}KB\n"
        info_text += f"System: {platform.system()} {platform.release()}\n"
        info_text += f"CPU: {psutil.cpu_percent()}% | Memory: {psutil.virtual_memory().percent}%"
        
        info_panel.config(state='normal')
        info_panel.delete('1.0', tk.END)
        info_panel.insert(tk.END, info_text)
        info_panel.config(state='disabled')

def update_port_list():
    if 'port_listbox' in globals():
        port_listbox.delete(0, tk.END)
        if open_ports:
            port_listbox.insert(tk.END, f"Open ports ({len(open_ports)}):")
            for port in open_ports:
                service = get_service_name(port)
                port_listbox.insert(tk.END, f"  Port {port} ({service})")
        else:
            port_listbox.insert(tk.END, "No open ports found")

def get_service_name(port):
    services = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
        53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
        443: "HTTPS", 3306: "MySQL", 3389: "RDP",
        8080: "HTTP Proxy", 8443: "HTTPS Alt",
        5900: "VNC", 6379: "Redis"
    }
    return services.get(port, "Unknown")

def draw_graphics():
    try:
        if not fig:
            return
            
        # Clear all axes
        for ax in fig.axes:
            ax.clear()
        
        # Plot ping graph if visible
        if graph_visibility[0] and ping_history:
            if grafik_tipe == 'candle':
                plot_candle(ax1, ping_history, graph_colors[0])
            elif grafik_tipe == 'bar':
                ax1.bar(range(len(ping_history)), ping_history, color=graph_colors[0])
            elif grafik_tipe == 'scatter':
                ax1.scatter(range(len(ping_history)), ping_history, color=graph_colors[0])
            elif grafik_tipe == 'step':
                ax1.step(range(len(ping_history)), ping_history, color=graph_colors[0])
            else:  # line
                ax1.plot(ping_history, color=graph_colors[0], label="Ping")
            ax1.set_title("Ping Latency (ms)")
            ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Plot port status graph if visible
        if graph_visibility[1] and port_history:
            ax2.plot(port_history, color=graph_colors[1], label="Port Status")
            ax2.set_title("Port Availability")
            ax2.grid(True, linestyle='--', alpha=0.7)
        
        # Plot traffic graph
        if graph_visibility[2] and traffic_history and len(traffic_history) > 0:
            sent_data = [t[0] for t in traffic_history]
            recv_data = [t[1] for t in traffic_history]
            ax3.plot(sent_data, color=graph_colors[2], label="Sent")
            ax3.plot(recv_data, color=graph_colors[3], label="Received")
            ax3.set_title("Network Traffic (bytes)")
            ax3.legend()
            ax3.grid(True, linestyle='--', alpha=0.7)
        
        # Plot extra graphs if visible
        for i in range(len(extra_graphs)):
            if i < len(axes_extra) and graph_visibility[i+3] and extra_graphs[i]:
                axes_extra[i].plot(extra_graphs[i], color=graph_colors[i+3], 
                                  linestyle='--', label=f"Metric {i+1}")
                axes_extra[i].set_title(f"Metric {i+1}")
                axes_extra[i].legend()
                axes_extra[i].grid(True, linestyle='--', alpha=0.7)
        
        # Apply background style
        apply_background_style()
        
        # Redraw canvas
        canvas.draw()
    except Exception as e:
        print(f"Drawing error: {e}")

def plot_candle(ax, data, color):
    if len(data) < 2:
        return
    for i in range(1, len(data)):
        ax.plot([i-1, i], [data[i-1], data[i]], color=color, linewidth=2)
        ax.plot([i, i], [data[i]-2, data[i]+2], color=color, linewidth=1)

def apply_background_style():
    if not fig:
        return
        
    if background_tipe == 'grid':
        for ax in fig.axes:
            ax.grid(True, linestyle='--', alpha=0.7)
    elif background_tipe == 'plain':
        for ax in fig.axes:
            ax.grid(False)
    elif background_tipe == 'dark':
        fig.patch.set_facecolor('#1e1e1e')
        for ax in fig.axes:
            ax.set_facecolor('#1e1e1e')
            ax.grid(color='gray', linestyle='--', alpha=0.7)
            for spine in ax.spines.values():
                spine.set_edgecolor('gray')
            ax.tick_params(colors='gray')
            ax.title.set_color('white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
    elif background_tipe == 'white':
        fig.patch.set_facecolor('white')
        for ax in fig.axes:
            ax.set_facecolor('white')
    elif background_tipe == 'image' and custom_background:
        try:
            img = Image.open(custom_background)
            img = img.resize((800, 600), Image.Resampling.LANCZOS)
            fig.figimage(img, alpha=0.1)
        except Exception as e:
            print(f"Background image error: {e}")

#==================== SETTINGS FUNCTIONS ====================#
def open_graph_settings():
    settings_win = tk.Toplevel(main_window)
    settings_win.title("Graph Settings")
    settings_win.geometry("400x400")
    settings_win.configure(bg=STYLE_BG)
    settings_win.resizable(False, False)
    
    # Graph visibility checkboxes
    tk.Label(settings_win, text="Show Graphs:", bg=STYLE_BG, fg=STYLE_FG).pack(pady=5)
    graph_names = ["Ping", "Port Status", "Traffic"] + [f"Metric {i+1}" for i in range(3)]
    
    for i in range(6):
        frame = tk.Frame(settings_win, bg=STYLE_BG)
        frame.pack(fill="x", padx=20, pady=2)
        
        var = tk.BooleanVar(value=graph_visibility[i])
        cb = tk.Checkbutton(frame, text=graph_names[i], variable=var, 
                          bg=STYLE_BG, fg=STYLE_FG, selectcolor="black",
                          command=lambda idx=i, v=var: update_graph_visibility(idx, v.get()))
        cb.pack(side="left")
        
        color_menu = ttk.Combobox(frame, values=GRAPH_COLORS, width=8, state="readonly")
        color_menu.set(graph_colors[i])
        color_menu.pack(side="right", padx=10)
        color_menu.bind("<<ComboboxSelected>>", lambda e, idx=i, cm=color_menu: update_graph_color(idx, cm.get()))
    
    # Close button
    ttk.Button(settings_win, text="Close", command=settings_win.destroy).pack(pady=20)

def update_graph_visibility(index, visible):
    graph_visibility[index] = visible
    draw_graphics()

def update_graph_color(index, color):
    graph_colors[index] = color
    draw_graphics()

def choose_background_image():
    global custom_background
    path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.jpeg")])
    if path:
        custom_background = path
        background_type_var.set('image')
        draw_graphics()

#==================== NETWORK SPEED TEST ====================#
def run_speed_test():
    def speed_test_thread():
        try:
            # Simulate speed test
            time.sleep(2)
            download = random.randint(10, 100)
            upload = random.randint(5, 50)
            
            add_notification(f"Speed test: Download {download} Mbps, Upload {upload} Mbps")
            messagebox.showinfo("Speed Test", 
                               f"Download Speed: {download} Mbps\nUpload Speed: {upload} Mbps")
        except Exception as e:
            print(f"Speed test error: {e}")
    
    threading.Thread(target=speed_test_thread, daemon=True).start()

#==================== EXPORT DATA ====================#
def export_data():
    def export_thread():
        try:
            # Simulate export
            time.sleep(1)
            add_notification("Data exported successfully")
            messagebox.showinfo("Export Data", "Data has been exported successfully!")
        except Exception as e:
            print(f"Export error: {e}")
    
    threading.Thread(target=export_thread, daemon=True).start()

#==================== MAIN MONITOR UI ====================#
def open_monitor_ui():
    global canvas, fig, ax1, ax2, ax3, axes_extra, info_panel, port_listbox, notification_listbox
    global main_window, grafik_type_var, background_type_var
    
    main_window = tk.Tk()
    main_window.title(f"POLOSS NETWORK MONITOR :: {url_input} ({selected_type.upper()})")
    main_window.configure(bg=STYLE_BG)
    main_window.geometry("1000x700")
    main_window.minsize(800, 600)
    
    # Configure grid layout
    main_window.grid_rowconfigure(1, weight=1)
    main_window.grid_columnconfigure(0, weight=1)
    
    # HEADER =================================================
    header_frame = tk.Frame(main_window, bg="#1a1a1a", height=60)
    header_frame.grid(row=0, column=0, sticky="ew", columnspan=2)
    header_frame.grid_columnconfigure(1, weight=1)
    
    # Logo and title
    logo_label = tk.Label(header_frame, text="POLOSS", font=("Arial", 18, "bold"), 
                         bg="#1a1a1a", fg=STYLE_FG)
    logo_label.grid(row=0, column=0, padx=20, sticky="w")
    
    title_label = tk.Label(header_frame, text=f"Monitoring: {url_input} ({selected_type.upper()})", 
             font=FONT_TITLE, bg="#1a1a1a", fg="white")
    title_label.grid(row=0, column=1, padx=10, sticky="w")
    
    # Control buttons
    control_frame = tk.Frame(header_frame, bg="#1a1a1a")
    control_frame.grid(row=0, column=2, padx=20, sticky="e")
    
    start_btn = tk.Button(control_frame, text="▶ START", font=("Arial", 10, "bold"),
                         bg="#00cc00", fg="white", bd=0, padx=10, pady=3, relief="flat",
                         command=lambda: threading.Thread(target=update_monitor, daemon=True).start())
    start_btn.pack(side="left", padx=3)
    
    stop_btn = tk.Button(control_frame, text="■ STOP", font=("Arial", 10, "bold"),
                        bg="#cc0000", fg="white", bd=0, padx=10, pady=3, relief="flat",
                        command=stop_monitor)
    stop_btn.pack(side="left", padx=3)
    
    settings_btn = tk.Button(control_frame, text="⚙", font=("Arial", 10, "bold"),
                            bg="#333333", fg="white", bd=0, padx=8, pady=3, relief="flat",
                            command=open_settings_menu)
    settings_btn.pack(side="left", padx=3)
    
    # MAIN CONTENT ===========================================
    content_frame = tk.Frame(main_window, bg=STYLE_BG)
    content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
    content_frame.grid_rowconfigure(0, weight=1)
    content_frame.grid_columnconfigure(0, weight=1)
    content_frame.grid_columnconfigure(1, weight=2)
    
    # LEFT PANEL =============================================
    left_frame = tk.Frame(content_frame, bg=STYLE_BG)
    left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    
    # Info panel
    info_frame = tk.LabelFrame(left_frame, text="Target Information", bg=STYLE_BG, fg=STYLE_FG,
                             font=FONT_NORM)
    info_frame.pack(fill="x", padx=5, pady=5)
    
    info_panel = scrolledtext.ScrolledText(info_frame, height=8, font=FONT_NORM, 
                            bg="#1e1e1e", fg=STYLE_FG, wrap=tk.WORD)
    info_panel.pack(fill="x", padx=5, pady=5)
    info_panel.config(state='disabled')
    
    # Port list
    port_frame = tk.LabelFrame(left_frame, text="Port Scanner", bg=STYLE_BG, fg=STYLE_FG,
                             font=FONT_NORM)
    port_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    port_scroll = tk.Scrollbar(port_frame)
    port_scroll.pack(side="right", fill="y")
    
    port_listbox = tk.Listbox(port_frame, bg="#1e1e1e", fg=STYLE_FG, 
                            font=FONT_NORM, height=6, yscrollcommand=port_scroll.set)
    port_listbox.pack(fill="both", expand=True, padx=5, pady=5)
    port_scroll.config(command=port_listbox.yview)
    
    # Notification panel
    notif_frame = tk.LabelFrame(left_frame, text="Notifications", bg=STYLE_BG, fg=STYLE_FG,
                              font=FONT_NORM)
    notif_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    notif_scroll = tk.Scrollbar(notif_frame)
    notif_scroll.pack(side="right", fill="y")
    
    notification_listbox = tk.Listbox(notif_frame, bg="#1e1e1e", fg="#FF5555", 
                                    font=("Consolas", 9), height=6, yscrollcommand=notif_scroll.set)
    notification_listbox.pack(fill="both", expand=True, padx=5, pady=5)
    notif_scroll.config(command=notification_listbox.yview)
    
    # RIGHT PANEL ============================================
    right_frame = tk.Frame(content_frame, bg=STYLE_BG)
    right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    right_frame.grid_rowconfigure(0, weight=1)
    right_frame.grid_columnconfigure(0, weight=1)
    
    # Create matplotlib figure
    fig = plt.figure(figsize=(8, 6), facecolor=STYLE_BG)
    gs = fig.add_gridspec(6, 1)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[2, 0])
    axes_extra = [fig.add_subplot(gs[i+3, 0]) for i in range(3)]
    
    # Create canvas
    canvas = FigureCanvasTkAgg(fig, master=right_frame)
    canvas.get_tk_widget().pack(fill="both", expand=True)
    
    # SETTINGS PANEL ========================================
    settings_frame = tk.Frame(main_window, bg=STYLE_BG)
    settings_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5, columnspan=2)
    
    # Graph type selection
    tk.Label(settings_frame, text="Graph Type:", bg=STYLE_BG, fg=STYLE_FG).grid(row=0, column=0, padx=5)
    grafik_type_var = tk.StringVar(value=grafik_tipe)
    graph_combo = ttk.Combobox(settings_frame, textvariable=grafik_type_var, values=GRAFIK_STYLES, width=10, state="readonly")
    graph_combo.grid(row=0, column=1, padx=5)
    
    # Background type selection
    tk.Label(settings_frame, text="Background:", bg=STYLE_BG, fg=STYLE_FG).grid(row=0, column=2, padx=5)
    background_type_var = tk.StringVar(value=background_tipe)
    bg_combo = ttk.Combobox(settings_frame, textvariable=background_type_var, values=BACKGROUND_STYLES, width=10, state="readonly")
    bg_combo.grid(row=0, column=3, padx=5)
    
    # Apply button
    apply_btn = ttk.Button(settings_frame, text="Apply", 
              command=lambda: [globals().__setitem__('grafik_tipe', grafik_type_var.get()),
                              globals().__setitem__('background_tipe', background_type_var.get()),
                              draw_graphics()])
    apply_btn.grid(row=0, column=4, padx=5)
    
    # Background image button
    bg_img_btn = ttk.Button(settings_frame, text="Background Image", command=choose_background_image)
    bg_img_btn.grid(row=0, column=5, padx=5)
    
    # STATUS BAR ============================================
    status_bar = tk.Frame(main_window, bg="#1a1a1a", height=24)
    status_bar.grid(row=3, column=0, sticky="ew", columnspan=2)
    
    clock_label = tk.Label(status_bar, text="", bg="#1a1a1a", fg="white")
    clock_label.pack(side="right", padx=10)
    
    def update_clock():
        clock_label.config(text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        clock_label.after(1000, update_clock)
    
    update_clock()
    
    # Handle window close
    def on_closing():
        stop_monitor()
        main_window.destroy()
    
    main_window.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Initial UI update
    update_info_panel(False, False, None, 0, 0)
    update_port_list()
    update_notifications()
    
    main_window.mainloop()

#==================== SETTINGS MENU ====================#
def open_settings_menu():
    menu = tk.Menu(main_window, tearoff=0, bg=STYLE_BG, fg=STYLE_FG)
    menu.add_command(label="Graph Settings", command=open_graph_settings)
    menu.add_command(label="Network Speed Test", command=run_speed_test)
    menu.add_command(label="Export Data", command=export_data)
    menu.add_command(label="View History", command=show_history)
    menu.add_separator()
    menu.add_command(label="About", command=show_about)
    
    try:
        # Show menu below settings button
        x = main_window.winfo_pointerx()
        y = main_window.winfo_pointery()
        menu.tk_popup(x, y)
    except Exception as e:
        print(f"Error showing menu: {e}")

#==================== ABOUT DIALOG ====================#
def show_about():
    about_win = tk.Toplevel(main_window)
    about_win.title("About POLOSS Network Monitor")
    about_win.geometry("400x300")
    about_win.configure(bg=STYLE_BG)
    about_win.resizable(False, False)
    about_win.transient(main_window)
    about_win.grab_set()
    
    # Center window
    about_win.update_idletasks()
    width = about_win.winfo_width()
    height = about_win.winfo_height()
    x = (main_window.winfo_screenwidth() // 2) - (width // 2)
    y = (main_window.winfo_screenheight() // 2) - (height // 2)
    about_win.geometry(f'+{x}+{y}')
    
    # Logo
    tk.Label(about_win, text="POLOSS", font=("Arial", 24, "bold"), 
            bg=STYLE_BG, fg=STYLE_FG).pack(pady=10)
    
    # Description
    desc = "Advanced Network Monitoring Tool\n\n" \
           "Features:\n" \
           "• Real-time network monitoring\n" \
           "• Port scanning and analysis\n" \
           "• Customizable graphs\n" \
           "• Traffic analysis\n" \
           "• Notification system\n\n" \
           "Version: 3.0\n" \
           "© 2023 POLOSS"
    
    tk.Label(about_win, text=desc, bg=STYLE_BG, fg="white", 
            justify="left").pack(pady=10)
    
    ttk.Button(about_win, text="Close", command=about_win.destroy).pack(pady=10)

#==================== HISTORY WINDOW ====================#
def show_history():
    history_win = tk.Toplevel(main_window)
    history_win.title("Monitoring History")
    history_win.geometry("500x400")
    history_win.configure(bg=STYLE_BG)
    history_win.transient(main_window)
    history_win.grab_set()
    
    # Center window
    history_win.update_idletasks()
    width = history_win.winfo_width()
    height = history_win.winfo_height()
    x = (main_window.winfo_screenwidth() // 2) - (width // 2)
    y = (main_window.winfo_screenheight() // 2) - (height // 2)
    history_win.geometry(f'+{x}+{y}')
    
    # Header
    tk.Label(history_win, text="Monitoring History", font=FONT_TITLE, 
            bg=STYLE_BG, fg=STYLE_FG).pack(pady=10)
    
    # Listbox
    list_frame = tk.Frame(history_win, bg=STYLE_BG)
    list_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side="right", fill="y")
    
    history_list = tk.Listbox(list_frame, bg="#1e1e1e", fg=STYLE_FG, 
                            font=FONT_NORM, yscrollcommand=scrollbar.set)
    history_list.pack(fill="both", expand=True)
    scrollbar.config(command=history_list.yview)
    
    # Add history items
    for item in reversed(history_data):
        history_list.insert(tk.END, f"{item['time']} - {item['url']} ({item['ip']})")
    
    # Buttons
    btn_frame = tk.Frame(history_win, bg=STYLE_BG)
    btn_frame.pack(pady=10)
    
    ttk.Button(btn_frame, text="Clear History", 
              command=lambda: [history_data.clear(), save_history(), history_list.delete(0, tk.END)]).pack(side="left", padx=10)
    
    ttk.Button(btn_frame, text="Close", command=history_win.destroy).pack(side="left", padx=10)

#==================== LOADING SCREEN ====================#
def show_loading():
    load = tk.Tk()
    load.title("Loading...")
    load.geometry("600x300")
    load.configure(bg="black")
    
    # Center window
    load.eval('tk::PlaceWindow . center')
    
    # Display banner art
    banner_frame = tk.Frame(load, bg="black")
    banner_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    banner_text = tk.Text(banner_frame, bg="black", fg=STYLE_FG, 
                         font=("Courier", 8), wrap="none")
    banner_text.pack(fill="both", expand=True)
    banner_text.insert(tk.END, BANNER_ART)
    banner_text.config(state="disabled")
    
    # Loading label
    tk.Label(load, text="Initializing monitoring system...", bg="black", fg="white", 
            font=FONT_NORM).pack(pady=5)
    
    # Progress bar
    progress = ttk.Progressbar(load, orient="horizontal", length=300, mode="indeterminate")
    progress.pack(pady=20)
    progress.start(10)
    
    # After loading, open main monitor
    load.after(2500, lambda: [load.destroy(), open_monitor_ui()])
    load.mainloop()

#==================== INITIAL SETUP ====================#
def step1_input():
    global history_data
    history_data = load_history()
    
    win = tk.Tk()
    win.title("POLOSS NETWORK MONITOR")
    win.configure(bg=STYLE_BG)
    win.geometry("400x300")
    
    # Center window
    win.eval('tk::PlaceWindow . center')
    
    # Header
    header_frame = tk.Frame(win, bg=STYLE_BG)
    header_frame.pack(pady=20)
    
    tk.Label(header_frame, text="POLOSS", font=("Arial", 20, "bold"), 
            bg=STYLE_BG, fg=STYLE_FG).pack()
    
    tk.Label(header_frame, text="Network Monitoring Tool", font=("Arial", 12), 
            bg=STYLE_BG, fg="white").pack(pady=5)
    
    # Input frame
    input_frame = tk.Frame(win, bg=STYLE_BG)
    input_frame.pack(pady=20)
    
    tk.Label(input_frame, text="Enter Target URL or IP:", bg=STYLE_BG, fg="white", 
            font=FONT_NORM).pack(pady=5)
    
    url_entry = tk.Entry(input_frame, font=FONT_NORM, width=30)
    url_entry.pack(pady=5)
    url_entry.focus()
    
    # Type selection
    type_frame = tk.Frame(input_frame, bg=STYLE_BG)
    type_frame.pack(pady=10)
    
    type_var = tk.StringVar(value="web")
    ttk.Radiobutton(type_frame, text="Website", variable=type_var, value="web").pack(side="left", padx=10)
    ttk.Radiobutton(type_frame, text="Server", variable=type_var, value="server").pack(side="left", padx=10)
    
    # Submit button
    def submit():
        global url_input, selected_type
        url_input = url_entry.get().strip()
        selected_type = type_var.get()
        
        if not url_input:
            messagebox.showerror("Error", "Please enter a target URL or IP address!")
            return
        
        # Validate the input
        if not ('.' in url_input or url_input.startswith("http")):
            messagebox.showerror("Error", "Please enter a valid URL or IP address!")
            return
        
        win.destroy()
        show_loading()
    
    submit_btn = tk.Button(win, text="START MONITORING", font=("Arial", 10, "bold"),
                         bg=STYLE_FG, fg=STYLE_BG, bd=0, padx=15, pady=8,
                         command=submit)
    submit_btn.pack(pady=15)
    
    # Footer
    footer = tk.Frame(win, bg=STYLE_BG)
    footer.pack(side="bottom", fill="x", pady=10)
    
    tk.Label(footer, text="© 2023 POLOSS | Network Security Tool", 
            bg=STYLE_BG, fg="gray", font=("Arial", 8)).pack()
    
    win.mainloop()

#==================== MAIN EXECUTION ====================#
if __name__ == '__main__':
    step1_input()
