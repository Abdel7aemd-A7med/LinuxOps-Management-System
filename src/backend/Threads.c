#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>
#include<sys/syscall.h>

     /* we simulate a bank system with 3 threads (monitor - bill - transfer) and it will change in account balance , we use mutex (lock) for mutual variables (global) to prevent race of conditions
       and make each thread complete its role and change the balance and release the lock to make the other threads change in the balance */

double account_balance = 5000.0; // global variable (mutual between all threads)
pthread_mutex_t bank_vault;     // declare mutex (lock)


void *monitor(void *arg){   // this function monitor the balance and print a statement if it has changed

    pthread_setname_np(pthread_self(),"monitor"); // to set a name for this thread in memory
    double updated_balance = account_balance ;
    printf("\n....monitor system started.......\n");

    while(1){ // this loop makes the thread get the lock and release it quickly to monitor the balance

        pthread_mutex_lock(&bank_vault);
        double current_balance = account_balance;
        pthread_mutex_unlock(&bank_vault);
        if(updated_balance!=current_balance) {  printf(".....your balance has changed....\n"); updated_balance=current_balance;   }
        usleep(500000);

    }

    return NULL;
}


void *long_transfer(void *arg) { // it simulates as a transfer process between accounts
    sleep(1);
     pthread_setname_np(pthread_self(),"transfer"); // to set name for thread in memory
    printf("🌍 International Transfer request started...\n");
    
    pthread_mutex_lock(&bank_vault); // to get the lock of balance
    printf("   🔒 [transfer Task] Acquired Lock. Verifying security protocols...\n");

    for(int i=1; i<=30; i++) { // it simulates the actual transfer by sleeping 30 seconds 
        printf("      ... verifying step %d/30 ...\n", i);
        sleep(1); 
    }

    if (account_balance >= 2000) { // to deduce balance
        account_balance -= 2000;
        printf("✅ [transfer Task] Transfer Complete! Deduced 2000 EGP.\n");
    } 
    
    printf("   🔓 [transfer Task] Releasing Lock.\n");
    pthread_mutex_unlock(&bank_vault); // release lock 
    return NULL;

}

void *bill(void *arg) { // it acts as pay a bill process
    sleep(2); 
        pthread_setname_np(pthread_self(),"bill"); // set name for thread
    printf("📄 [bill Task] Bill Payment request started...\n");

    pthread_mutex_lock(&bank_vault); // get lock of balance
    printf("   🔒 [bill Task] Acquired Lock. Processing bill...\n");

    sleep(15); // sleep 15 sec

    if (account_balance >= 500) {  //deduce balance
        account_balance -= 500;
        printf("✅ [bill Task] Bill Paid! Deduced 500 EGP.\n");
    } 

    printf("   🔓 [bill Task] Releasing Lock.\n");
    pthread_mutex_unlock(&bank_vault); //release lock
    return NULL;
}


int main() {
    setbuf(stdout,NULL);
    
    // get id of program
    int pid = getpid();
  FILE *g = fopen("/home/abdelhamed/project/multi-thread-program/program_id.txt","w");
  fprintf(g,"%d",pid);
  fflush(g);
  fclose(g);

    pthread_t t_long, t_medium, t_monitor;  // declare threads 

    pthread_mutex_init(&bank_vault, NULL); // declare lock

    printf("--- Bank System Online. Initial Balance: %.2f ---\n\n", account_balance);

     // crate threads
    pthread_create(&t_monitor, NULL, monitor, NULL);
    pthread_create(&t_long, NULL, long_transfer, NULL);
    pthread_create(&t_medium, NULL,bill, NULL);
    
    // prevent program from closing untill threads complete its task
    pthread_join(t_long, NULL);
    pthread_join(t_medium, NULL);
    pthread_join(t_monitor, NULL);

    printf("\n--- System Shutdown. Final Balance: %.2f ---\n", account_balance);
    pthread_mutex_destroy(&bank_vault); // destroy lock
    return 0;
}