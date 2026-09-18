ERROR    | 2026-09-17 06:33:34,227 | angr.state_plugins.unicorn_engine | failed loading "unicornlib.dylib", unicorn support disabled ('NoneType' object has no attribute 'unicorn_py3')
// ---- 0x14362d300
double sub_14362d300(void* a0, long long a1, long long a2, long long a3, long long a4)
{
    unsigned int v1;  // r9d
    int v2;  // xmm4
    char v3;  // cl
    int v4;  // xmm6
    int v5;  // xmm1
    int v6;  // xmm3
    int v7;  // xmm0
    int v8;  // xmm0
    int v9;  // xmm1

    v1 = *((int *)a0) >> 8;
    v2 = (int)(*((int *)a0) & 0xff);
    v3 = (char)a1 * 6;
    v4 = (int)(*((int *)(a2 + (char *)a0)) & 0xff);
    v5 = (int)(MulV(v1 >> (v3 & 31) & 63, 1015154721));
    if (!((CmpF(*((unsigned int *)&v6), 0) & 69) >> 2 & 1) && CmpF(*((unsigned int *)&v6), 0) & 64)
        return *((unsigned long long *)&AddV(MulV(AddV(MulV(SubV(v4, v2), v5), v2), *(a4)), a4[1]));
    if (a1 >= 3)
    {
        v8 = SubV(*(2 * a2 + (char *)a0), v4);
        v9 = (int)(MulV(*((int *)(a2 + (char *)a0)) >> 8 & 63, 1015154721));
        return *((unsigned long long *)&AddV(MulV(AddV(MulV(SubV(AddV(MulV(v8, v9), v4), AddV(MulV(SubV(v4, v2), v5), v2)), v6), AddV(MulV(SubV(v4, v2), v5), v2)), *(a4)), a4[1]));
    }
    v7 = (int)(MulV(v1 >> (v3 + 6 & 31) & 63, 1015154721));
    return *((unsigned long long *)&AddV(MulV(AddV(MulV(AddV(MulV(SubV(v7, v5), v6), v5), SubV(v4, v2)), v2), *(a4)), a4[1]));
}

// ---- 0x14362cdb0
typedef struct st_14362cdb0_0 {
    unsigned short field_0;
    unsigned short field_2;
    char field_3;
    char field_4[2];
    char field_5;
    unsigned short field_6;
} st_14362cdb0_0;

double sub_14362cdb0(void* a0, long long a1, long long a2, long long a3, long long a4)
{
    unsigned long v2;  // r9
    st_14362cdb0_0 *v3;  // r11
    unsigned int v12;  // r9d
    int v14;  // xmm3
    unsigned int v15;  // edx
    unsigned int v16;  // ecx
    int v18;  // xmm3
    unsigned int v19;  // edx
    unsigned int v20;  // ecx
    unsigned int v4;  // edx
    int v22;  // xmm3
    unsigned int v5;  // r8d
    unsigned long long v6;  // rbx
    unsigned int v7;  // ebx
    int v8;  // xmm2
    int v9;  // xmm3
    int v10;  // xmm1
    unsigned short v11;  // dx
    unsigned long long v0;  // [bp-0x8]

    v2 = a2;
    v3 = (char *)a0 + v2;
    if (!a1)
    {
        v19 = a0->field_0;
        v20 = a0->field_2 & 0xfff;
        v22 = MulV(ConvI32StoF32x4((unsigned int)((*((short *)&a0->field_3) & 0xfff) - v20)), v9);
        return *((unsigned long long *)&AddV(MulV(AddV(MulV(DivV(AddV(v22, ConvI32StoF32x4(v20)), 0x457ff000), ConvI32StoF32x4((unsigned int)(v3->field_0 - v19))), ConvI32StoF32x4(v19)), *(a4)), a4[1]));
    }
    v4 = a1 - 1;
    if (a1 == 1)
    {
        v15 = a0->field_0;
        v16 = *((short *)&a0->field_3) & 0xfff;
        v18 = MulV(ConvI32StoF32x4((unsigned int)((*((short *)&a0->field_4[1]) & 0xfff) - v16)), v9);
        return *((unsigned long long *)&AddV(MulV(AddV(MulV(DivV(AddV(v18, ConvI32StoF32x4(v16)), 0x457ff000), ConvI32StoF32x4((unsigned int)(v3->field_0 - v15))), ConvI32StoF32x4(v15)), *(a4)), a4[1]));
    }
    else if (v4 == 1)
    {
        v11 = *((short *)&a0->field_4[1]);
        v12 = a0->field_0;
        v14 = MulV(ConvI32StoF32x4((a0->field_4[0] & 240 | a0->field_2 >> 12 | v11 >> 4 & 0xf00) - (v11 & 0xfff)), v9);
        return *((unsigned long long *)&AddV(MulV(AddV(MulV(DivV(AddV(v14, ConvI32StoF32x4(v11 & 0xfff)), 0x457ff000), ConvI32StoF32x4((unsigned int)(v3->field_0 - v12))), ConvI32StoF32x4(v12)), *(a4)), a4[1]));
    }
    else if (v4 == 2)
    {
        v5 = a0->field_0;
        v0 = v6;
        v7 = v3->field_0;
        v8 = (int)(AddV(DivV(MulV(ConvI32StoF32x4((*((short *)&a0->field_4[1]) & 61455 | *((char *)&a0->field_2 + 1)) >> 4 | a0->field_4[0] & 240), ConvI32StoF32x4((v7 & 0xffff) - v5)), 0x457ff000), ConvI32StoF32x4(v5)));
        if (!((CmpF(*((unsigned int *)&v9), 0) & 69) >> 2 & 1) && CmpF(*((unsigned int *)&v9), 0) & 64)
            return *((unsigned long long *)&AddV(MulV(v8, *(a4)), a4[1]));
        v10 = (int)(DivV(MulV((unsigned int)((&a0->field_0)[v2] - v7), v3->field_2 & 0xfff), 0x457ff000));
        return *((unsigned long long *)&AddV(MulV(AddV(MulV(SubV(AddV(v10, v7), v8), v9), v8), *(a4)), a4[1]));
    }
    else
    {
        return 0;
    }
}

// ---- 0x14362d430
unsigned int * sub_14362d430(void* a0, unsigned int a1, int a2, unsigned long a3, unsigned int a4, unsigned int *a5, unsigned int *a6, unsigned int a7)
{
    int v1;  // xmm5
    int v2;  // xmm8
    unsigned int v3;  // r9d
    unsigned int v4;  // r10d
    char v5;  // cl
    int v6;  // xmm6
    int v7;  // xmm7
    int v8;  // xmm3
    unsigned int v9;  // zmm2

    v1 = (int)a4;
    v2 = (int)(*((int *)a0) & 0xff);
    v3 = *((int *)a0) >> 8;
    v4 = *((int *)(a2 + (char *)a0));
    v5 = (char)a1 * 6;
    v6 = (int)(v4 & 0xff);
    v7 = SubV(v6, v2);
    v9 = (unsigned int)(AddV(MulV(AddV(MulV(MulV(v3 >> (v5 & 31) & 63, 1015154721), v7), v2), v8), v1));
    *(a5) = v9;
    if (!((CmpF(a7, 0) & 69) >> 2 & 1) && CmpF(a7, 0) & 64)
    {
        *(a6) = v9;
        return a6;
    }
    if (a1 < 3)
        *(a6) = *((unsigned int *)&AddV(MulV(AddV(MulV(MulV(v3 >> (v5 + 6 & 31) & 63, 1015154721), v7), v2), v8), v1));
    else
        *(a6) = *((unsigned int *)&AddV(MulV(AddV(MulV(SubV(*(2 * a2 + (char *)a0), v6), MulV(v4 >> 8 & 63, 1015154721)), v6), v8), v1));
    return a6;
}

// ---- 0x14362d040
typedef struct st_14362d040_0 {
    unsigned short field_0;
    char field_2[2];
    char field_3;
    char field_4[2];
    char field_5;
    unsigned short field_6;
} st_14362d040_0;

unsigned int * sub_14362d040(st_14362d040_0 *idx, unsigned int a1, int a2, unsigned int *a3, unsigned int *a4, unsigned int *a5, unsigned int a6)
{
    unsigned long v1;  // rbx
    st_14362d040_0 *v2;  // r11
    unsigned int v11;  // eax
    unsigned int v12;  // r8d
    int v13;  // xmm0
    unsigned int v14;  // ecx
    unsigned int v15;  // eax
    int v16;  // xmm1
    unsigned short v17;  // ax
    unsigned int v18;  // ecx
    unsigned int v19;  // eax
    unsigned int v3;  // edx
    unsigned int v4;  // r8d
    unsigned short v5;  // dx
    unsigned int v6;  // zmm2
    unsigned int v7;  // ecx
    uint128_t v8;  // xmm1
    unsigned int *v9;  // rax
    unsigned int v10;  // ecx

    v1 = a2;
    v2 = v1 + (char *)idx;
    if (!a1)
    {
        v18 = idx->field_0;
        v19 = v2->field_0 - v18;
        *(a4) = AddV(MulV(AddV(DivV(MulV(ConvI32StoF32x4(v19), ConvI32StoF32x4((uint128_t)(idx->field_2 & 0xfff))), 0x457ff000), ConvI32StoF32x4(v18)), *(a3)), a3[1]);
        v7 = idx->field_0;
        v16 = (int)(unsigned int)(v2->field_0 - v7);
        v17 = *((short *)&idx->field_3);
        goto LABEL_14362d2b1;
    }
    v3 = a1 - 1;
    if (a1 != 1)
    {
        if (v3 != 1)
        {
            if (v3 != 2)
                return v9;
            v4 = idx->field_0;
            v5 = *((short *)&idx->field_4[1]) & 61455 | idx->field_2[1];
            v6 = AddV(MulV(AddV(DivV(MulV(ConvI32StoF32x4(v5 >> 4 | idx->field_4[0] & 240), ConvI32StoF32x4((unsigned int)(v2->field_0 - v4))), 0x457ff000), ConvI32StoF32x4(v4)), *(a3)), a3[1]);
            *(a4) = v6;
            if (!((CmpF(a6, 0) & 69) >> 2 & 1) && CmpF(a6, 0) & 64)
            {
                *(a5) = v6;
                return a5;
            }
            v7 = v2->field_0;
            v8 = DivV(MulV((unsigned int)((&v2->field_0)[v1 >> 1] - v7), ConvI32StoF32x4((uint128_t)(v2->field_2 & 0xfff))), 0x457ff000);
LABEL_14362d2cd:
            v13 = (int)v7;
        }
        else
        {
            v10 = idx->field_0;
            v11 = v2->field_0 - v10;
            *(a4) = AddV(MulV(AddV(DivV(MulV(ConvI32StoF32x4(v11), ConvI32StoF32x4(*((short *)&idx->field_4[1]) & 0xfff)), 0x457ff000), ConvI32StoF32x4(v10)), *(a3)), a3[1]);
            v12 = idx->field_0;
            v13 = (int)v12;
            v8 = DivV(MulV(ConvI32StoF32x4((idx->field_2[1] | *((short *)&idx->field_4[1]) & 61455) >> 4 | idx->field_4[0] & 240), ConvI32StoF32x4((unsigned int)(v2->field_0 - v12))), 0x457ff000);
        }
        *(a5) = AddV(MulV(AddV(v8, ConvI32StoF32x4(v13)), *(a3)), a3[1]);
        return a5;
    }
    v14 = idx->field_0;
    v15 = v2->field_0 - v14;
    *(a4) = AddV(MulV(AddV(DivV(MulV(ConvI32StoF32x4(v15), ConvI32StoF32x4(*((short *)&idx->field_3) & 0xfff)), 0x457ff000), ConvI32StoF32x4(v14)), *(a3)), a3[1]);
    v7 = idx->field_0;
    v16 = (int)(unsigned int)(v2->field_0 - v7);
    v17 = *((short *)&idx->field_4[1]);
LABEL_14362d2b1:
    v8 = DivV(MulV(ConvI32StoF32x4(v16), ConvI32StoF32x4(v17 & 0xfff)), 0x457ff000);
    goto LABEL_14362d2cd;
}

// ---- 0x14362ccd0
double sub_14362ccd0(long long a0, long long a1, long long a2, void* a3, int a4, long long idx)
{
    unsigned long v6;  // rax
    unsigned long v7;  // r8
    int v8;  // xmm0
    int v0;  // [bp-0x58]
    int v1;  // [bp-0x48]
    char v2;  // [bp-0x38]
    char v3;  // [bp-0x28]
    char v4;  // [bp-0x18]

    v6 = a2;
    v7 = a1 * 4 + 4;
    if (3 > a1)
        v6 = v7;
    v0 = (int)(CONCAT(CONCAT(idx[6], idx[4]), CONCAT(idx[2], *(idx))));
    v1 = (int)(CONCAT(CONCAT(idx[7], idx[5]), CONCAT(idx[3], idx[1])));
    sub_1436146c0();
    sub_1436146c0(&v2, *((int *)(v6 + (char *)a0)), &v1, &v0);
    v8 = (int)*((int128_t *)sub_143613b20(&v4, &v3, &v2));
    *(a3) = (uint128_t)v8;
    return *((unsigned long long *)&v8);
}

// ---- 0x14362cbf0
typedef struct st_14362cbf0_0 {
    char padding_0[6];
    unsigned short field_6;
} st_14362cbf0_0;

void sub_14362cbf0(st_14362cbf0_0 *a0)
{
    if (a0->field_6 != 1)
        goto LABEL_0x14362cc04;
    return;
}

// ---- 0x1436214a0
extern unsigned int g_145f7ea40;
extern uint128_t g_145f807f0;
extern int g_145f80800;

double sub_1436214a0(void* idx)
{
    uint128_t v6;  // xmm7
    uint128_t v7;  // xmm8
    int v16;  // xmm6
    int v17;  // xmm4
    int v18;  // xmm3
    int v19;  // xmm4
    int v20;  // xmm5
    int v21;  // xmm3
    unsigned long v8;  // gs
    unsigned int v9;  // zmm3
    unsigned int v10;  // zmm2
    unsigned int v11;  // zmm1
    uint128_t v12;  // xmm7
    uint128_t v13;  // xmm8
    int v14;  // xmm1
    int v15;  // xmm0
    int v0;  // [bp-0x68]
    char v1;  // [bp-0x58]
    char v2;  // [bp-0x48]
    uint128_t v3;  // [bp-0x38]
    uint128_t v4;  // [bp-0x28]

    v4 = v6;
    v3 = v7;
    if (g_145f80800 > *((int *)(389424 + *((long long *)(*((long long *)(88 + v8)) + g_145f7ea40 * 8)))))
    {
        sub_1435d9e60(&g_145f80800);
        if (g_145f80800 == -0x1)
        {
            g_145f807f0 = (uint128_t)0x3f8000003f0000003f0000003f000000;
            sub_1435d9e00(&g_145f80800);
        }
    }
    v0 = (int)(CONCAT(CONCAT(0x3f800000, v9), CONCAT(v10, v11)) * g_145f807f0);
    sub_143621db0(&v0, &v2, &v1);
    v12 = v1;
    v13 = v2;
    v14 = (int)(CONCAT(CONCAT((unsigned int)(v12 >> 64), (unsigned int)(v12 >> 64)), CONCAT((unsigned int)(v12 >> 64), (unsigned int)(v12 >> 64))));
    v15 = (int)(CONCAT(CONCAT((unsigned int)((unsigned long long)v12 >> 32), (unsigned int)((unsigned long long)v12 >> 32)), CONCAT((unsigned int)((unsigned long long)v12 >> 32), (unsigned int)((unsigned long long)v12 >> 32))));
    v16 = MulV(v14, v15);
    v17 = (int)(CONCAT(CONCAT((unsigned int)(v13 >> 64), (unsigned int)(v13 >> 64)), CONCAT((unsigned int)(v13 >> 64), (unsigned int)(v13 >> 64))));
    v18 = (int)(CONCAT(CONCAT((unsigned int)((unsigned long long)v13 >> 32), (unsigned int)((unsigned long long)v13 >> 32)), CONCAT((unsigned int)((unsigned long long)v13 >> 32), (unsigned int)((unsigned long long)v13 >> 32))));
    v19 = MulV(v17, v15);
    v20 = MulV(v17, v18);
    v21 = MulV(v18, v14);
    *(idx) = *((unsigned int *)&SubV(MulV(v13, v16), MulV(v12, v20)));
    idx[1] = *((unsigned int *)&AddV(MulV(v13, v19), MulV(v12, v21)));
    idx[3] = *((unsigned int *)&AddV(MulV(v13, v20), MulV(v12, v16)));
    idx[2] = *((unsigned int *)&SubV(MulV(v12, v19), MulV(v13, v21)));
    return *((unsigned long long *)&MulV(v13, v21));
}

