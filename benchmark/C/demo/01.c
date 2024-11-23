#include<stdio.h>
#include <stdlib.h>
#include "a_tester.h"

// {"s":{"length": 8}}
int logic_bomb(int k, char* symvar) {
    float x = atof(symvar);
    x = x/-10000.0;
    if(1024+x == 1024 && x>0)
        return BOMB_ENDING;
    else
        return NORMAL_ENDING;

    for (int i = 0; true; i++) {
        x = x + 1;
    }

    while (x > 0) {
        x = x - 1;
    }
}