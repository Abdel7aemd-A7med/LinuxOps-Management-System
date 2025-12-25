#include<stdio.h>
#include<stdlib.h>
#include<unistd.h>
#include<string.h>
int main(){
    
    // to get id of process
int pid = getpid();

printf("the id is %d\n",pid);


int chunk = 30*1024*1024; //this is the value that will be consumed in cumulative way every time (30 mega)

while(1){

    char *ptr = (char*)malloc(chunk); //allocate memory into (ptr) to consume it

    if(ptr != NULL){ 
        memset(ptr,0,chunk);  //to consume real memory not virtual , we write zeros into this space
    }

    sleep(1); //consume 30 mega every 2 seconds
}


    return 0;
}