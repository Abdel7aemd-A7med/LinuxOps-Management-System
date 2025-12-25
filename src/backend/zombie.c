#include<stdio.h>
#include<unistd.h>
#include<stdlib.h>
#include<sys/types.h>
int main(){

pid_t pid = fork(); // to create child 

if( pid > 0 ){ // make parent sleep all the time to prevent him from using ( wait() system call) to know state of the child , if he knows child is dead he remnoves him from memory
    while(1) {sleep(5);}
   }

    if(pid==0){ //get id of child and parent 

    FILE *f=fopen("/home/abdelhamed/project/zombie-process/child_proces_id.txt","w");
    fprintf(f,"%d",getpid());
     fclose(f);

    FILE *g=fopen("/home/abdelhamed/project/zombie-process/parent_proces_id.txt","w");
     fprintf(g,"%d",getppid());
     fclose(g);

        exit(0); //kill child , it will wait for his parent to wake up and remove him from memory  (zombie state)
    }
    return 0;
}