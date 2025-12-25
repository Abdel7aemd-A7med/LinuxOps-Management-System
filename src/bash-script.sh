#!/bin/bash

# --- تعريف الألوان ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- قائمة أسماء البرامج (لازم تطابق أسماء الملفات التنفيذية عندك) ---
MY_PROGS=("CPUHOG" "MEMHOG" "zombie" "orphan" "IDLE" "Threads")

# ==============================================================================
# 1. دالة عرض العمليات (Robust View Function)
# ==============================================================================
view_my_processes() {
    echo -e "\n${CYAN}--- [ Your Active Processes ] ---${NC}"
    
    # تجميع الـ PIDs الخاصة ببرامجنا فقط
    PIDS=""
    for prog in "${MY_PROGS[@]}"; do
        # pgrep -f يبحث عن الاسم في سطر الأوامر بالكامل
        found=$(pgrep -f "$prog")
        if [ ! -z "$found" ]; then
            PIDS="$PIDS $found"
        fi
    done

    # تنظيف المسافات الزائدة
    PIDS=$(echo $PIDS | xargs)

    # التحقق: هل القائمة فارغة؟ (هنا كان بيحصل الإيرور زمان)
    if [ -z "$PIDS" ]; then
        echo -e "${RED}No active processes found.${NC}"
        return 1
    fi

    # تحويل المسافات لفواصل عشان ps يقبلها (لبعض التوزيعات)
    PIDS_COMMA=$(echo $PIDS | tr ' ' ',')

    # عرض الجدول
    printf "${YELLOW}%-8s %-15s %-6s %-6s %-6s %-8s %-10s${NC}\n" "PID" "NAME" "STATE" "PRI" "NI" "CPU%" "MEM(KB)"
    echo "------------------------------------------------------------------"
    ps -p "$PIDS_COMMA" -o pid,comm,state,pri,ni,pcpu,rss --no-headers
    echo "------------------------------------------------------------------"
    return 0
}

# ==============================================================================
# 2. دالة التشغيل (Launch Menu)
# ==============================================================================
launch_menu() {
    echo -e "\n${YELLOW}[ Launch New Process ]${NC}"
    echo "1) CPU Hog   (High CPU Load)"
    echo "2) Memory Hog (High RAM Load)"
    echo "3) Zombie    (Defunct Process)"
    echo "4) Orphan    (Parent Dies)"
    echo "5) Idle      (Sleeping)"
    echo "6) threads             "
    echo "0) Back"
    read -p "Select process to create: " l_choice

    case $l_choice in
        1) ./CPUHOG & ;;
        2) ./MEMHOG & ;;
        3) ./zombie & ;;
        4) ./orphan & ;;
        5) ./IDLE & ;; 
        6) ./Threads & ;;
        0) return ;;
        *) echo -e "${RED}Invalid choice${NC}" ;;
    esac
    
    # رسالة تأكيد
    if [ $? -eq 0 ] && [ "$l_choice" != "0" ]; then
        echo -e "${GREEN}Process Launched Successfully in Background!${NC}"
        sleep 1
    fi
}

# ==============================================================================
# 3. دالة التحكم (Manage Processes)
# ==============================================================================
manage_process() {
    ACTION_TYPE=$1 # نستقبل نوع العملية (PAUSE, RESUME, KILL, RENICE)

    # 1. عرض الجدول عشان المستخدم يعرف يختار الـ PID
    view_my_processes
    if [ $? -ne 0 ]; then return; fi # لو مفيش عمليات نخرج

    # 2. طلب الـ PID
    echo -e "\n${BLUE}Enter PID to $ACTION_TYPE (or '0' to cancel):${NC}"
    read target_pid

    if [ "$target_pid" == "0" ]; then return; fi

    # التأكد إن المدخل أرقام فقط
    if [[ ! "$target_pid" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}Error: Invalid PID!${NC}"
        sleep 1; return
    fi

    # 3. تنفيذ الأمر
    case $ACTION_TYPE in
        "PAUSE")
            kill -STOP "$target_pid" && echo -e "${GREEN}Process $target_pid Paused.${NC}"
            ;;
        "RESUME")
            kill -CONT "$target_pid" && echo -e "${GREEN}Process $target_pid Resumed.${NC}"
            ;;
        "KILL")
            echo "  1) Terminate (SIGTERM - Safe)"
            echo "  2) Force Kill (SIGKILL - Instant)"
            read -p "  Method: " k_method
            if [ "$k_method" == "1" ]; then
                kill -15 "$target_pid" && echo -e "${GREEN}Sent SIGTERM to $target_pid.${NC}"
            elif [ "$k_method" == "2" ]; then
                kill -9 "$target_pid" && echo -e "${GREEN}Sent SIGKILL to $target_pid.${NC}"
            fi
            ;;
        "RENICE")
            read -p "  Enter new Nice value (-20 to 19): " n_val
            if [ "$n_val" -lt 0 ]; then
                # لو القيمة سالبة نطلب sudo
                sudo renice -n "$n_val" -p "$target_pid"
            else
                renice -n "$n_val" -p "$target_pid"
            fi
            ;;
    esac
    read -p "Press Enter to continue..."
}

# ==============================================================================
# 4. الحلقة الرئيسية (Main Loop)
# ==============================================================================
while true; do
    clear
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}      🐧 FINAL PROCESS MANAGER 🐧       ${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # عداد سريع للعمليات الشغالة
    count=$(pgrep -f "CPUHOG|MEMHOG|zombie|orphan|IDLE|Threads" | wc -l)
    echo -e "Running Processes: ${GREEN}$count${NC}"
    echo "----------------------------------------"
    
    echo "1. 🟢 Launch Process"
    echo "2. 📋 List Processes"
    echo "3. ⏸  Pause (Suspend)"
    echo "4. ▶  Resume (Continue)"
    echo "5. ⚖  Renice (Priority)"
    echo "6. 💀 Kill / Terminate"
    echo "7. 🧹 Kill ALL (Cleanup)"
    echo "0. 🚪 Exit"
    echo "----------------------------------------"
    read -p "Your Choice: " choice

    case $choice in
        1) launch_menu ;;
        2) view_my_processes; read -p "Press Enter..." ;;
        3) manage_process "PAUSE" ;;
        4) manage_process "RESUME" ;;
        5) manage_process "RENICE" ;;
        6) manage_process "KILL" ;;
        7) 
            pkill -f CPUHOG; pkill -f MEMHOG; pkill -f zombie; pkill -f orphan; pkill -f IDLE; pkill -f Threads;
            echo -e "${GREEN}All project processes killed.${NC}"
            sleep 1
            ;;
        0) echo "Goodbye!"; break ;;
        *) echo "Invalid Option"; sleep 1 ;;
    esac
done
