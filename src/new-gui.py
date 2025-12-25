import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import threading
import time
import signal
from collections import deque
import os
import random
import errno

# paths for programs
CPU_HOG_CMD = "/home/abdelhamed/project/CPU-HOG-process/process/CPUHOG"
IDLE_CMD = "/home/abdelhamed/project/idle-process/process/IDLE"
ZOMBIE_CMD = "/home/abdelhamed/project/zombie-process/process/zombie"
THREADS_CMD = "/home/abdelhamed/project/multi-thread-program/program/Threads"
ORPHAN_CMD = "/home/abdelhamed/project/orphan-process/process/orphan"
MEMORY_HOG_CMD = "/home/abdelhamed/project/MEMORY-HOG-process/MEMORY-HOG"

# Colors for frames or windows of program
BG_MAIN = "#1E1E1E"
BG_PANEL = "#252526"
FG_TEXT = "#E6E6E6"
ACCENT_BLUE = "#007ACC"
ACCENT_RED = "#F14C4C"

# colors for state
STATE_COLORS = {
    'RUNNING': "#2ECC71",  # Green: Active on CPU (Delta Time > 0)
    'WAITING': "#F1C40F",  # Yellow: Runnable but Queueing (Context Switch)
    'SLEEPING': "#444444", # Gray: Sleeping/Idle
    'STOPPED': "#E74C3C",  # Red: Paused/Stopped
    'ZOMBIE': "#9B59B6",   # Purple: Defunct Process
}

class ProcessMonitorApp:
    def __init__(self, root):
        self.root = root #declare the window of program
        self.root.title("LinuxOps Managment")  # title of window
        self.root.geometry("1400x900") # size of window
        self.root.configure(bg=BG_MAIN)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing) # when i press exit or (x) sign , apply (on_closing) function

        # State
        self.pause_refresh = False
        self.chart_mode = "gantt" # default displayed chart
        self.process_history = {} 
        self.prev_cputimes = {} 
        self.launched_pids = set() # Stores PIDs we launched (Parents)
        self.max_history = 80
        
        # start (graphics of program)
        self.setup_styles()
        self.create_top_panel()
        self.create_center_panel()
        self.create_bottom_panel()
        
        # Start of program
        self.running = True
        self.update_thread = threading.Thread(target=self.fetch_loop, daemon=True) # (daemon) makes the thread finish its task when program is closing
        self.update_thread.start()
        
        self.log("=== Monitor Started ===") 

   # function declares style of program
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=BG_PANEL, foreground=FG_TEXT, fieldbackground=BG_PANEL, rowheight=28, borderwidth=0)
        style.map("Treeview", background=[('selected', ACCENT_BLUE)])
        style.configure("Treeview.Heading", background="#333333", foreground="white", font=('Segoe UI', 10, 'bold'))


   # create top panel of program
    def create_top_panel(self):
        top_frame = tk.Frame(self.root, bg=BG_PANEL, height=50)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tk.Label(top_frame, text="Process Monitor & Managment", 
                 bg=BG_PANEL, fg=FG_TEXT, font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT, padx=10)
        
        self.filter_var = tk.BooleanVar(value=True)

        # create check button to display my processes (zombie - orphan - multi thread - sleepy ....) 
        chk = tk.Checkbutton(top_frame, text="Display My Processes", variable=self.filter_var,
                             bg=BG_PANEL, fg=ACCENT_BLUE, selectcolor=BG_PANEL, activebackground=BG_PANEL, font=("Arial", 11, "bold"))
        chk.pack(side=tk.RIGHT, padx=10)


   # create  central part of program ( table of processes - gantt chart - chart of cpu usage - toggle button between between theee two charts)
    def create_center_panel(self):
        # We use a main container to hold the paned window and leave space for the bottom panel
        self.center_container = tk.Frame(self.root, bg=BG_MAIN)
        self.center_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.paned_window = tk.PanedWindow(self.center_container, orient=tk.VERTICAL, bg=BG_MAIN, sashwidth=4, sashrelief=tk.FLAT)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Upper Split: Table and Charts
        top_split = tk.PanedWindow(self.paned_window, orient=tk.VERTICAL, bg=BG_MAIN)
        
        # create table
        table_frame = tk.Frame(top_split, bg=BG_PANEL)
        columns = ("PID", "PPID" , "COMMAND", "CPU%", "MEM", "STATE", "PRI", "NI") 
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.tree.heading("PID", text="PID"); self.tree.column("PID", width=50, anchor="center")
        self.tree.heading("PPID", text="PPID"); self.tree.column("PPID", width=60, anchor="center")
        self.tree.heading("COMMAND", text="COMMAND"); self.tree.column("COMMAND", width=150, anchor="w")
        self.tree.heading("CPU%", text="CPU%"); self.tree.column("CPU%", width=60, anchor="center")
        self.tree.heading("MEM", text="MEM(MB)"); self.tree.column("MEM", width=70, anchor="center")
        self.tree.heading("STATE", text="ACTUAL STATE"); self.tree.column("STATE", width=100, anchor="center")
        self.tree.heading("PRI", text="PRI"); self.tree.column("PRI", width=50, anchor="center")
        self.tree.heading("NI", text="NI"); self.tree.column("NI", width=50, anchor="center")
        
        # Create menu to display two options (child - threads) when we press right click on any process in table
        self.popup_menu = tk.Menu(self.tree, tearoff=0)
        self.popup_menu.add_command(label="Show Children (Forks)", command=self.show_kids_simple)
        self.popup_menu.add_command(label="Show Threads (LWP)", command=self.show_threads_simple)
        self.tree.bind("<Button-3>", self.do_right_click)
        
        # create scroll bar of table
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        top_split.add(table_frame, height=200) # RATIONAL SIZE for Table

        # create charts and toggle button between them
        self.chart_frame = tk.Frame(top_split, bg=BG_PANEL, bd=1, relief=tk.SOLID)
        chart_header = tk.Frame(self.chart_frame, bg=BG_PANEL)
        chart_header.pack(fill=tk.X, padx=5, pady=2)
        
        self.legend_frame = tk.Frame(chart_header, bg=BG_PANEL)
        self.legend_frame.pack(side=tk.LEFT)
        
        self.mode_btn = tk.Button(chart_header, text="Switch to Load Chart", bg="#444", fg="white", 
                                  font=("Arial", 9), command=self.toggle_chart_mode)
        self.mode_btn.pack(side=tk.RIGHT)

        self.canvas = tk.Canvas(self.chart_frame, bg="#111", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        top_split.add(self.chart_frame, height=250) # RATIONAL SIZE for Chart
        self.paned_window.add(top_split)

        # --- New Panel: Process Output Console (Bigger size as requested) ---
        output_frame = tk.Frame(self.paned_window, bg=BG_MAIN)
        output_header = tk.Frame(output_frame, bg=BG_MAIN)
        output_header.pack(fill=tk.X)
        
        tk.Label(output_header, text="Processes Terminal Output", bg=BG_MAIN, fg=ACCENT_BLUE, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Clear button for the output window
        tk.Button(output_header, text=" Clear Output ", bg="#333", fg="#AAA", font=("Arial", 8), 
                  relief=tk.FLAT, command=self.clear_output).pack(side=tk.RIGHT, padx=5)

        self.output_text = tk.Text(output_frame, bg="#000000", fg="#FFFFFF", font=("Consolas", 10), state="disabled")
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.paned_window.add(output_frame, height=180) # RATIONAL SIZE for Output

        # Create bottom log console (Minimized)
        console_frame = tk.Frame(self.paned_window, bg=BG_MAIN)
        self.console_text = tk.Text(console_frame, bg="#1E1E1E", fg="#00FF00", font=("Consolas", 9), state="disabled")
        self.console_text.pack(fill=tk.BOTH, expand=True)
        self.paned_window.add(console_frame, height=70) # RATIONAL SIZE for Console
        
        self.update_legend() 

    # the two lower function to create and update legend of the two charts (gantt / cpu load)
    def create_legend_item(self, parent, text, color):
        f = tk.Frame(parent, bg=BG_PANEL)
        f.pack(side=tk.LEFT, padx=8)
        tk.Label(f, bg=color, width=2, height=1).pack(side=tk.LEFT)
        tk.Label(f, text=text, bg=BG_PANEL, fg="#CCC", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)

    def update_legend(self):
        for widget in self.legend_frame.winfo_children():
            widget.destroy()
        if self.chart_mode == "gantt":
            self.create_legend_item(self.legend_frame, "EXEC (Green)", STATE_COLORS['RUNNING'])
            self.create_legend_item(self.legend_frame, "QUEUE (Yell)", STATE_COLORS['WAITING'])
            self.create_legend_item(self.legend_frame, "ZOMBIE (Purp)", STATE_COLORS['ZOMBIE'])
        else:
            tk.Label(self.legend_frame, text="CPU Usage (%)", bg=BG_PANEL, fg="#AAA", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
    

    # create bottom part of program 
    def create_bottom_panel(self):
        btn_frame = tk.Frame(self.root, bg=BG_PANEL, height=60)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

         # function to create button
        def make_btn(parent, text, color, cmd):
            return tk.Button(parent, text=text, bg=color, fg="white", font=("Arial", 9, "bold"), relief=tk.FLAT, width=11, command=cmd)

        left = tk.Frame(btn_frame, bg=BG_PANEL); left.pack(side=tk.LEFT, padx=5, pady=5)
        make_btn(left, "cpu-Hog", ACCENT_RED, lambda: self.launch_process(CPU_HOG_CMD, "Hungry-cpu")).pack(side=tk.LEFT, padx=1)
        make_btn(left, "memory-Hog", ACCENT_RED, lambda: self.launch_process(MEMORY_HOG_CMD, "Hungry-memory")).pack(side=tk.LEFT, padx=1)
        make_btn(left, "Idle", "#34495E", lambda: self.launch_process(IDLE_CMD, "Sleepy")).pack(side=tk.LEFT, padx=1)
        make_btn(left, "Zombie", "#9B59B6", lambda: self.launch_process(ZOMBIE_CMD, "Zombie")).pack(side=tk.LEFT, padx=1)
        make_btn(left, "Orphan", "#9B59B6", lambda: self.launch_process(ORPHAN_CMD, "Orphan")).pack(side=tk.LEFT, padx=1)
        make_btn(left, "Threads", "#E67E22", lambda: self.launch_process(THREADS_CMD, "Threader")).pack(side=tk.LEFT, padx=1)

        center = tk.Frame(btn_frame, bg=BG_PANEL); center.pack(side=tk.LEFT, padx=5, pady=5)
        make_btn(center, "⏸ Pause", "#E67E22", self.stop_process).pack(side=tk.LEFT, padx=1)
        make_btn(center, "▶ Resume", "#2ECC71", self.resume_process).pack(side=tk.LEFT, padx=1)
        make_btn(center, "⚖ Renice", "#009688", self.renice_selected).pack(side=tk.LEFT, padx=1)
        make_btn(center, "🛑 SIGTERM", "#C0392B", self.kill_term).pack(side=tk.LEFT, padx=1)
        make_btn(center, "💀 SIGKILL", "#8B0000", self.kill_kill).pack(side=tk.LEFT, padx=1)

        right = tk.Frame(btn_frame, bg=BG_PANEL); right.pack(side=tk.RIGHT, padx=5, pady=5)
        make_btn(right, "Kill All", "#555", self.kill_all_launched).pack(side=tk.LEFT, padx=2)

    # function to fetch in loop (monitor processes all the time)
    def fetch_loop(self):
        while self.running:
            if not self.pause_refresh:
                self.fetch_processes()
            time.sleep(0.1) # Fast sampling 

    # function to fetch state and info of processes and split two displays for all processes or only my processes
    def fetch_processes(self):
        try:
            cmd = ["ps", "-eo", "pid,ppid,comm,times,pcpu,rss,state,pri,ni,args", "--no-headers"] # command that return info of process
            output = subprocess.check_output(cmd).decode("utf-8") # decode output because the returned value of command in bytes 
            
            rows = [] # declare list to store info of each process in it
            strict_my_processes = ["CPUHOG", "zombie","MEMHOG","orphan", "IDLE", "Threads"] # processes that will be displayed in (my processes show)
            
            for line in output.splitlines():  # to split values from returned result from command (remove any string or non wanted outputs)
                parts = line.split()
                if len(parts) < 10: continue
                if not parts[0].isdigit(): continue 

                pid = int(parts[0])
                ppid = int(parts[1])
                cmd_name = parts[2]
                
                try: cputime = int(parts[3])
                except: cputime = 0
                try: pcpu = float(parts[4].replace(',', '.'))
                except: pcpu = 0.0
                try: rss_kb = float(parts[5])
                except: rss_kb = 0.0
                mem_mb = f"{rss_kb/1024:.2f}"
                
                state_raw = parts[6]
                state_char = state_raw[0]
                pri = parts[7]
                ni = parts[8]
                full_cmd = " ".join(parts[9:])
                
                is_my_process = False
                
                if pid in self.launched_pids: # ensure to display any process i created  
                    is_my_process = True
                if ppid in self.launched_pids: # ensure to display any process i created its parent  (zombie state)
                    is_my_process = True

                else:
                    for proc_name in strict_my_processes:
                        if proc_name == cmd_name or proc_name in full_cmd:
                            is_my_process = True
                            break
                
                if self.filter_var.get() and not is_my_process: continue

                prev_time = self.prev_cputimes.get(pid, cputime) # get previous time of process on cpu (like number of seconds)
                self.prev_cputimes[pid] = cputime # get current time of process
                delta_time = cputime - prev_time # if delta time = 0 it means process is queued else it is running
                
                # determine state of process that will be shown  (state_char is from returned result from command)
                final_state = "SLEEPING"
                if state_char == 'T': final_state = "STOPPED"
                elif state_char == 'Z': final_state = "ZOMBIE" # Now Zombies will appear!
                elif state_char == 'R':
                    if delta_time > 0: final_state = "RUNNING"
                    else: final_state = "WAITING"
                else: final_state = "SLEEPING"

                rows.append((pid, ppid, cmd_name, pcpu, mem_mb, final_state, pri, ni)) # prepare data will be displayed and updated
                self.update_history(pid, cmd_name, final_state, pcpu) # update info of processes into charts

          # the next try and except handels important case (orphan) , it makes the python code removes any process he is the parent of it and the process terminated by (waitpid())
            try:
                while True:
                    pid,status = os.waitpid(-1 , os.WNOHANG)
                    if pid == 0 : break
            except ChildProcessError:
                pass    


            self.root.after(0, self.update_table, rows) # constant function ast as scheduled task or timer that do task (update table ) every specific time 
            self.root.after(0, self.draw_chart) # to update chart (call draw_chart  every 0 seconds or when it is avalibale to call it)
        except Exception as e: print(f"Error: {e}")


    # function to update state of processes if we sent signal for it (in table)
    def update_table(self, rows):
        sel = self.tree.selection()
        selected_pid = self.tree.item(sel[0])['values'][0] if sel else None
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            state = r[4]
            tags = ()
            if state == 'RUNNING': tags = ('running',)
            elif state == 'WAITING': tags = ('waiting',)
            elif state == 'STOPPED': tags = ('stopped',)
            elif state == 'ZOMBIE': tags = ('zombie',)
            
            item = self.tree.insert("", "end", values=r, tags=tags)
            if selected_pid and r[0] == selected_pid: self.tree.selection_set(item)
        
        self.tree.tag_configure('running', foreground=STATE_COLORS['RUNNING'])
        self.tree.tag_configure('waiting', foreground=STATE_COLORS['WAITING'])
        self.tree.tag_configure('stopped', foreground=STATE_COLORS['STOPPED'])
        self.tree.tag_configure('zombie', foreground=STATE_COLORS['ZOMBIE'])


   # function to update info of processes in charts
    def update_history(self, pid, name, state, pcpu):
        key = (pid, name)
        if key not in self.process_history:
            self.process_history[key] = deque([{'state': 'SLEEPING', 'cpu': 0.0}]*self.max_history, maxlen=self.max_history)
        self.process_history[key].append({'state': state, 'cpu': pcpu})


   # function of toggle button between two charts
    def toggle_chart_mode(self):
        if self.chart_mode == "gantt":
            self.chart_mode = "load"
            self.mode_btn.config(text="Switch to Gantt Chart")
        else:
            self.chart_mode = "gantt"
            self.mode_btn.config(text="Switch to Load Chart")
        self.update_legend()
        self.draw_chart()
   
   # function to draw the charts
    def draw_chart(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        process_usage_list = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            pid = int(values[0])
            try:
                usage = float(str(values[2]).replace('%', '')) 
            except:
                usage = 0.0
            process_usage_list.append((pid, usage))

        process_usage_list.sort(key=lambda x: x[1], reverse=True)
        top_7_pids = set(pid for pid, usage in process_usage_list[:7])

        active_items = []
        for (pid, name), history in self.process_history.items():
            if pid in top_7_pids:
                active_items.append(((pid, name), list(history)))

        active_items.sort(key=lambda x: x[0][0])
        
        if not active_items: 
            self.canvas.create_text(w/2, h/2, text="Launch Processes...", fill="#555")
            return

        step_x = w / self.max_history
 
        # part to draw gantt chart
        if self.chart_mode == "gantt":
            row_height = (h - 20) / len(active_items) if len(active_items) > 0 else 40
            if row_height > 60: row_height = 60
            for t in range(0, self.max_history, 10):
                x = w - (t * step_x)
                self.canvas.create_line(x, 0, x, h, fill="#222", dash=(1, 4))

            for idx, ((pid, name), history_data) in enumerate(active_items):
                y_top = idx * row_height
                y_bottom = y_top + row_height - 6
                self.canvas.create_rectangle(0, y_top, w, y_bottom+6, fill="#1A1A1A" if idx%2==0 else "#161616", outline="")
                self.canvas.create_text(5, y_top + row_height/2, text=f"{name} ({pid})", fill="white", anchor="w", font=("Arial", 10, "bold"))
                
                for time_idx, data_point in enumerate(history_data):
                    state = data_point['state']
                    x1 = time_idx * step_x
                    x2 = x1 + step_x
                    color = STATE_COLORS.get(state, STATE_COLORS['SLEEPING'])
                    if state in ['RUNNING', 'WAITING', 'STOPPED', 'ZOMBIE']:
                        self.canvas.create_rectangle(x1, y_top+2, x2, y_bottom-2, fill=color, outline="")
                    else:
                        mid_y = y_top + row_height/2   
                        self.canvas.create_line(x1, mid_y, x2, mid_y, fill=color, width=2)

         # part to draw cpu usage chart               
        else:
            for i in range(0, 101, 20):
                y = h - (i / 100 * h)
                self.canvas.create_line(0, y, w, y, fill="#333", dash=(2, 4))
                self.canvas.create_text(20, y, text=f"{i}%", fill="#666", font=("Arial", 8))
            colors = ["#FF3333", "#33FF57", "#3357FF", "#F033FF", "#FFFF33"]
            for idx, ((pid, name), history_data) in enumerate(active_items):
                color = colors[idx % len(colors)]
                points = []
                for time_idx, data_point in enumerate(history_data):
                    cpu_val = data_point['cpu']
                    x = time_idx * step_x
                    y = h - (cpu_val / 100 * h)
                    points.append(x); points.append(y)
                if len(points) >= 4: self.canvas.create_line(points, fill=color, width=2, smooth=True)
                last_cpu = history_data[-1]['cpu']
                self.canvas.create_text(w-10, 10 + (idx*15), text=f"{name}: {last_cpu}%", fill=color, anchor="e", font=("Arial", 9, "bold"))


   # function to run my processes and it is linked with buttons
    def launch_process(self, path, alias):
        def _run():  #create internal function to be called by threading (to make it thread )
            try:
                cmd = ["taskset", "-c", "0", path]  # command to run process on single core (core 0) , to enable us to see context swithch between processes
                try: subprocess.call(["which", "taskset"], stdout=subprocess.DEVNULL) # it searches for taskset program on linux to use cpu affinity 
                except: cmd = [path]
                
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) 
                self.launched_pids.add(proc.pid) # add id of my launched processes in list (launched pids)
                self.log(f"Launched {alias} (PID: {proc.pid}) on Core 0") # send updates to console

                # Real-time output capture loop
                for line in proc.stdout:
                    if not self.running: break
                    self.root.after(0, self.append_process_output, f"[{alias} - {proc.pid}]: {line}")
                
                proc.wait()
            except Exception as e: self.log(f"Failed: {e}")
        threading.Thread(target=_run, daemon=True).start() # to create a thread that handles looking for taskser program 

    # New helper function to append text to the process output panel
    def append_process_output(self, msg):
        self.output_text.configure(state='normal')
        self.output_text.insert(tk.END, msg)
        self.output_text.see(tk.END) # Auto-scroll to latest output
        self.output_text.configure(state='disabled')

    # function to clear the process output terminal
    def clear_output(self):
        self.output_text.configure(state='normal')
        self.output_text.delete('1.0', tk.END)
        self.output_text.configure(state='disabled')
        self.log("Process Output Cleared")

    # function to show children of any process
    def show_kids_simple(self):         # it is like lower function in explantion
        sel = self.tree.selection()
        if not sel: return
        try:
            pid = self.tree.item(sel[0])['values'][0]
            # Use strict error handling and parsing
            cmd = ["ps", "--ppid", str(pid), "-o", "pid,state,comm", "--no-headers"] #command to get children of selected process
            try:
                output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8")
                if output.strip():
                    msg = f"Children of {pid}:\n\n{'PID':<8} | {'State':<5} | {'Command'}\n" + "-"*35 + "\n"
                    for line in output.splitlines():
                        p = line.split(maxsplit=2)
                        # Fix parsing for different ps outputs
                        if len(p) >= 3:
                            msg += f"{p[0]:<8} | {p[1]:<5} | {p[2]}\n"
                        elif len(p) == 2:
                             msg += f"{p[0]:<8} | {p[1]:<5} | ?\n"
                    messagebox.showinfo(f"Children of {pid}", msg)
                else:
                    messagebox.showinfo("Info", "No children found.")
            except subprocess.CalledProcessError:
                messagebox.showinfo("Info", "No children found.")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    # function to show threads of process
    def show_threads_simple(self):
        sel = self.tree.selection() # to know which process has been chosen
        if not sel: return
        try:
            pid = self.tree.item(sel[0])['values'][0]
            cmd = ["ps", "-L", "-p", str(pid), "-o", "lwp,state,comm", "--no-headers"] #command to get threads of process
            try:
                output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8") #execute command and decode its ouput
                if output.strip():
                    msg = f"Threads of {pid}:\n\n{'TID':<8} | {'State':<5} | {'Name'}\n" + "-"*35 + "\n" # prepare format of displayed list of threads if it found
                    for line in output.splitlines():
                        p = line.split(maxsplit=2)
                        if len(p) >= 2: msg += f"{p[0]:<8} | {p[1]:<5} | {p[2] if len(p)>2 else ''}\n"
                    messagebox.showinfo(f"Threads of {pid}", msg)
                else:
                    messagebox.showinfo("Info", "No threads found.")
            except subprocess.CalledProcessError:
                messagebox.showinfo("Info", "No threads found.")
        except: pass
    

    # function to get pid of selected process from table
    def get_selected_pid(self):
        sel = self.tree.selection()   # get pid of selected process
        if not sel: return None
        return int(self.tree.item(sel[0])['values'][0])


    # function to renice any selected process
    def renice_selected(self):
        pid = self.get_selected_pid()  # use the upper function to get id of process to renice it
        if not pid: return
        val = simpledialog.askinteger("Renice", "Value (-20 to 19):", minvalue=-20, maxvalue=19) # display message to ask for value of renicing
        if val is None: return
        def _run(): # function to execute renicing (it sends the command)
            cmd = ["renice", "-n", str(val), "-p", str(pid)]  # command will be sent to id of process
            if val < 0: cmd.insert(0, "pkexec")  # if renice value lower than 0 , we order password of user 
            subprocess.call(cmd) # execute command
            self.log(f"Reniced {pid}") # to send update to console
        threading.Thread(target=_run).start()  # create thread to renice                       


    # function sends stop signal for selected process (stop button)
    def stop_process(self):
        pid = self.get_selected_pid()
        if pid:
            os.kill(pid, signal.SIGSTOP) 
            self.log(f"process {pid} has stopped")
        

    # function sends resume signal for selected process (resume button)
    def resume_process(self):
        pid = self.get_selected_pid()
        if pid:
            os.kill(pid, signal.SIGCONT) # sends the signal to id of process
            self.log(f"process {pid} will continue")


     # function sends kill signal for selected process (kill button)
    def kill_kill(self): 
        pid = self.get_selected_pid()
        if pid and messagebox.askyesno("SIGKILL", f"Force KILL {pid}?"):  # display message to ask to kill
            try: 
                os.kill(pid, signal.SIGKILL)  
                self.log(f"process {pid} has killed")
            except Exception as e: messagebox.showerror("Error", str(e))


   # function sends terminate signal for selected process   (terminate button)
    def kill_term(self): 
        pid = self.get_selected_pid()
        if pid and messagebox.askyesno("SIGTERM", f"Terminate {pid}?"): # display message to ask to terminate
            try: 
                os.kill(pid, signal.SIGTERM)
                self.log(f"process {pid} has terminated")
            except Exception as e: messagebox.showerror("Error", str(e))


     # function sends kill signal for any process has been launched by me  (kill all button)
    def kill_all_launched(self):
        for name in ["CPUHOG", "process", "zombie", "orphan", "program"]:
            subprocess.call(["pkill", "-f", name])  # to kill any process in my list
        self.log("Killed all") # it sends update to console


    # function to declare right click press
    def do_right_click(self, event):
        try:
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
                self.popup_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.popup_menu.grab_release()


    #function to display any updates for my processes
    def log(self, msg):
        self.console_text.configure(state='normal') # enable the console to write on it 
        self.console_text.insert(tk.END, f"> {msg}\n") # insert the latest update
        self.console_text.see(tk.END)   # enable show of console to move down
        self.console_text.configure(state='disabled')


    # function closes program and kill any launched processes by me
    def on_closing(self):
        self.running = False
        self.kill_all_launched() # kill any process has been launched by me
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ProcessMonitorApp(root)
    root.mainloop()