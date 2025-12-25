#include<stdio.h>
#include<unistd.h>
#include<stdlib.h>
#include<sys/types.h>

 // we create parent and in same time the parent create a child and terminate , when child

int main(){

pid_t pid = fork(); /* make parent creates a child  , pid_t  is like a card , we give a card to parent contains id of child 
                    and give a card contains 0 to child to make it know that he is the child*/

if( pid > 0 ){  // to terminate parent (who has a card its value not 0 (it is child id))
    exit(0);
   }

if(pid==0){  // get id of child (who has card its value is 0)
  sleep(1);

    FILE *f=fopen("/home/abdelhamed/project/orphan-process/child_process_id.txt","w");
    fprintf(f,"%d",getpid());
     fclose(f);
     
     while(1){sleep(3);}
    }
    
    return 0;
}