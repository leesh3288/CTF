#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

typedef unsigned long long ull;

ull a1 = 0x0000100a6b70fcd0;
ull a2 = 0x00001009b376ad6c;
ull a3 = 0x00000000004012d1;
ull a4 = 0x000000003b9aca07;
ull a5 = 0x00000000004013f7;
ull a6 = 0x00001009b375075f;
ull a7 = 0x000010098eacdca4;
ull a8 = 0x00000000004015b0;

uint8_t s1[0x2f];
uint64_t s2[6];

int main(void)
{
    s2[0] = 0x97D54FBB1A8B7E3BLL;
    s2[1] = 0x87FD66CBCFBE80A5LL;
    s2[2] = 0xE80DE41A07115875LL;
    s2[3] = 0xA50860421721908BLL;
    s2[4] = 0x7AA2645A89A03AF8LL;
    s2[5] = 0x00392438A7E2307DLL;

    memcpy(s1, s2, sizeof(s1));

    uint8_t *trace = malloc(0x1d000000ULL * 4);

    int cnt = 0;
    while (1) {
        a3 *= a5;
        a3 %= a4;
        if (a3 == a8)
            break;
        
        uint8_t v280 = (a2 ^ a3) % 0x2F;
        uint8_t v281 = (a6 ^ a3) % 0x2F;
        if (v280 != v281) {
            uint8_t v225 = (a1 ^ a7) % 5;
            trace[cnt*4 + 0] = v280;
            trace[cnt*4 + 1] = v281;
            trace[cnt*4 + 2] = v225;
            trace[cnt*4 + 3] = a3 & 0xff;
            cnt++;
        }
    
        a2 ^= a7;
        a6 ^= a1;
        a2 *= a2;
        a1 *= a2;
        a1 += a6;
        a7 += a1;
    }

    printf("cnt = %x\n", cnt);

    for (int i = cnt - 1; i >= 0; i--) {
        uint8_t a3, v280, v281, v225;
        v280 = trace[i*4 + 0];
        v281 = trace[i*4 + 1];
        v225 = trace[i*4 + 2];
        a3   = trace[i*4 + 3];
        if (v225 == 0) {
            s1[v280] -= a3;
            s1[v281] += a3;
        }
        else if (v225 == 1)
            s1[v280] ^= s1[v281];
        else if (v225 == 2)
            s1[v280] -= s1[v281];
        else if (v225 == 3)
            s1[v280] += s1[v281];
        else if (v225 == 4) {
            s1[v280] ^= s1[v281];
            s1[v281] ^= s1[v280];
            s1[v280] ^= s1[v281];
        }
    }

    // zer0pts{sc4110p_1s_my_m05t_fav0r1t3_su5h1_1t3m}
    printf("%s\n", s1);

    return 0;
}

/*
a1 = 0x0000100a6b70fcd0
a2 = 0x00001009b376ad6c
a3 = 0x00000000004012d1
a4 = 0x000000003b9aca07
a5 = 0x00000000004013f7
a6 = 0x00001009b375075f
a7 = 0x000010098eacdca4
a8 = 0x00000000004015b0

s1 = "..."

while True:
    a3 *= a5
    a3 %= a4
    if a3 == a8:
        break
        
    v280 = (a2 ^ a3) % 0x2F
    v281 = (a6 ^ a3) % 0x2F
    if v280 != v281:
        v225 = (a1 ^ a7) % 5
        if v225 == 0:
            s1[v280] += a3 & 0xFF
            s1[v281] -= a3 & 0xFF
        elif v225 == 1:
            s1[v280] ^= s1[v281]
        elif v225 == 2:
            s1[v280] += s1[v281]
        elif v225 == 3:
            s1[v280] -= s1[v281]
        elif v225 == 4:
            s1[v280] ^= s1[v281]
            s1[v281] ^= s1[v280]
            s1[v280] ^= s1[v281]
    
    a2 ^= a7
    a6 ^= a1
    a2 *= a2
    a1 *= a2
    a1 += a6
    a7 += a1
    
s2[0] = 0x97D54FBB1A8B7E3BLL;
s2[1] = 0x87FD66CBCFBE80A5LL;
s2[2] = 0xE80DE41A07115875LL;
s2[3] = 0xA50860421721908BLL;
s2[4] = 0x7AA2645A89A03AF8LL;
s2[5] = 0x392438A7E2307DLL;
if ( memcmp(s1, s2, 0x2FuLL) )
*/