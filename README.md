# 🐧 LinuxOps Management System

**LinuxOps** is a powerful system-level monitoring tool designed to visualize the internal mechanics of the Linux Kernel. By integrating a **Pyth** frontend with specialized **C-backend** simulators, the project provides a granular, real-time look into scheduling, resource contention, and process lifecycles.

---

## 🚀 Core Simulation Modules

The project features custom-built C programs to simulate real-world OS scenarios:

* **CPU Hog**: Executes intensive computational loops to stress the CPU and test scheduler fairness.
* **Memory Hog**: Allocates and manipulates RAM to monitor **Resident Set Size (RSS)** and memory management.
* **Zombie Process**: Demonstrates PID retention in the process table when a parent fails to call `wait()`.
* **Orphan Process**: Visualizes child process adoption by **init/systemd (PID 1)** after parent termination.
* **Multithreading**: Spawns multiple threads to explore **LWP (Lightweight Processes)** and shared resources.

---

## 📊 Technical Innovation: The Gantt Chart

The centerpiece of this tool is the real-time Gantt Chart, which visualizes the Linux Scheduler's work using advanced logic:

### **1. CPU Affinity Control**
The tool utilizes `taskset` to bind workloads to **Core 0**. This forces the Linux Kernel to perform frequent **Context Switches**, allowing users to witness true resource competition in a multitasking environment.
         <img width="1125" height="369" alt="image" src="https://github.com/user-attachments/assets/c232feea-6e8e-438c-85dd-8ee6308bf8e6" />


### **2. Delta-Time Analysis**
Using a custom algorithm (`current_cputime - prev_cputime`), the chart dynamically distinguishes between:
* **RUNNING (Green)**: The process is actively executing on the CPU.
* **WAITING (Yellow)**: The process is in a `Runnable` state but is currently queued by the scheduler.



---

## 🛠️ System Control & Automation

* **Signals Dispatcher**: Directly manage processes via Linux signals (**SIGSTOP**, **SIGCONT**, **SIGKILL**, **SIGTERM**).
* **Priority Tuning**: Dynamically adjust process niceness using the integrated **Renice** tool.
* **Bash Automation**: Includes **Bash Scripts** for automated environment bootstrapping and seamless C-backend compilation.

---

## 📂 Project Structure

```text
├── src/
│   ├── ProcessMonitorApp.py  # Main Python GUI (Tkinter)
│   └── backend/             # C source files for simulations
│       ├── CPUHOG.c
│       ├── MEMHOG.c
│       ├── zombie.c
│       ├── orphan.c
│       └── Threads.c
├── process/                 # Compiled binary executables (Ignored by Git)
├── scripts/                 # Bash scripts for setup and automation
└── docs/                    # Technical reports and Flowcharts
