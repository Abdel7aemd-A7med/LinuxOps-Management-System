#include<stdio.h>
#include<unistd.h>
#include<stdlib.h>
int main(){
    // to get id of process and write it in text file
    int pid = getpid();
    FILE *f= fopen("/home/abdelhamed/project/CPU-HOG-process/process_id.txt","w");
    fprintf(f,"%d",pid); 
    fflush(f);
    fclose(f);

 //loop will consume cpu

int i=200 , j=20;
while(1){ 

    i=i*j;

}
    return 0;
}