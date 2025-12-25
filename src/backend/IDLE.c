#include<stdio.h>
#include<unistd.h>
#include<stdlib.h>
#include<time.h>
#include<signal.h>

void clear_content(){ //this function writes nothing or remove any previous data in the text file

 FILE *f=fopen("/home/abdelhamed/project/idle-process/temp_data.txt","w");
 fclose(f);

}

void handle_sigterm(int sig){ //this function clears content of text file and terminates the process

clear_content();
exit(0);

}

void handle_sigkill(int sig){ //this function terminates the process without removing the content of text file

    clear_content(); //we call this function to prove that (sigkill) is not uninterruptible
    exit(0);

}

int main(){
    // to get id of process 
    int pid = getpid();
    FILE *f= fopen("/home/abdelhamed/project/idle-process/process_id.txt","w");
    fprintf(f,"%d",pid);
    fflush(f);
    fclose(f);
    
    //signal handling function (it determines how to deal with each signal) ,(it converts the signal to int value and assign it to the function  like SIGKILL is 9)
    signal(SIGTERM,handle_sigterm);
    signal(SIGKILL,handle_sigkill);
  

    // to print random number every 5 seconds in text file
    srand(time(NULL));
    while(1){
    FILE *g= fopen("/home/abdelhamed/project/idle-process/temp_data.txt","a");
    int random_value = (rand()%1000)+1;
    fprintf(g,"%d\n",random_value);
    fclose(g);
    sleep(5);
    }
    return 0;
}