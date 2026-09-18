ERROR    | 2026-09-17 06:23:48,797 | angr.state_plugins.unicorn_engine | failed loading "unicornlib.dylib", unicorn support disabled ('NoneType' object has no attribute 'unicorn_py3')
// ---- 0x143690040
typedef struct st_143690040_1 {
    unsigned long long field_0;
} st_143690040_1;

typedef struct st_143690040_2 {
    struct st_143690040_0 *field_0;
} st_143690040_2;

typedef struct st_143690040_0 {
    char padding_0[112];
    struct st_143690040_1 *field_70;
} st_143690040_0;

void sub_143690040(st_143690040_2 **a0, unsigned long a1, unsigned long a2, unsigned long a3)
{
    unsigned long long v9;  // rsi
    unsigned long long v10;  // rdi
    unsigned long long v11;  // r12
    unsigned long long v12;  // r13
    unsigned long long v13;  // r14
    unsigned long long v14;  // r15
    unsigned long long v15;  // rbx
    unsigned long long v0;  // [bp-0x40]
    unsigned long long v1;  // [bp-0x38]
    unsigned long long v2;  // [bp-0x30]
    unsigned long long v3;  // [bp-0x28]
    unsigned long long v4;  // [bp-0x20]
    unsigned long long v5;  // [bp-0x18]
    unsigned long long v6;  // [bp-0x10]
    st_143690040_2 **v7;  // [bp+0x8]
    unsigned long long v8;  // [bp+0x10]

    v7 = a0;
    v6 = v9;
    v5 = v10;
    v4 = v11;
    v3 = v12;
    v2 = v13;
    v1 = v14;
    v0 = 0xfffffffffffffffe;
    v8 = v15;
    *(a0)->field_0->field_70();
}

// ---- 0x143633e00
typedef struct st_143633e00_0 {
    unsigned int field_0;
    unsigned int field_4;
    char padding_8[2];
    short field_a;
    char padding_c[4];
    unsigned int field_10;
} st_143633e00_0;

typedef struct st_143633e00_1 {
    char padding_0[4];
    unsigned int field_4;
} st_143633e00_1;

extern void g_145f841d8;

int sub_143633e00(st_143633e00_0 *idx, st_143633e00_1 **a1, unsigned int a2)
{
    unsigned long long v8;  // rbp
    unsigned long long v9;  // rsi
    unsigned int v18;  // eax
    unsigned int v19;  // ecx
    unsigned int v20;  // esi
    unsigned int v21;  // eax
    unsigned long v22;  // rax
    unsigned long long v10;  // rdi
    unsigned long long v11;  // r14
    unsigned int v12;  // eax
    unsigned int v13;  // edx
    void* v14;  // rax
    unsigned int v15;  // eax
    void* ptr;  // rdi
    unsigned int v17;  // r14d
    int v0;  // [bp-0xb8]
    unsigned long long v1;  // [bp-0x28]
    char v2;  // [bp+0x8], Other Possible Types: unsigned int
    char v3;  // [bp+0x9]
    char v4;  // [bp+0xa]
    char v5;  // [bp+0xb]
    unsigned long long v6;  // [bp+0x10]
    unsigned long long v7;  // [bp+0x18]

    v8 = _INSERT(0, 0, 0);
    if (idx->field_0 > 2)
    {
        if (idx->field_0 - 0x1000000 <= 0x1000000)
        {
            v8 = _INSERT(v8, 0, 1);
        }
        else
        {
            *(a1) = NULL;
            return 0;
        }
    }
    v6 = v9;
    v7 = v10;
    v1 = v11;
    if (!a2)
    {
        v12 = sub_143632a50();
        v13 = idx->field_4;
        if ((char)v8)
        {
            *((char *)&v2 + 3) = v13;
            *((char *)&v2) = v13 >> 24;
            *((char *)&v2 + 1) = v13 >> 16;
            v13 = _INSERT(v2, 2, v13 >> 8);
            v2 = v13;
        }
        a2 = v13 + 32 + v12 * 28;
        v14 = sub_1435da860(a2);
    }
    else
    {
        v14 = *(a1);
    }
    v15 = (unsigned int)v14;
    ptr = v14;
    if (v15 & 3)
        ptr = ptr - (v15 & 3) + 4;
    *((void* *)&g_145f841d8) = ptr + 72;
    memset(ptr, 0, 72);
    sub_143633670(idx, ptr, v8 & 0xff, idx, v14);
    v17 = (unsigned int)(*((int *)&g_145f841d8) - v14);
    v18 = v17;
    if ((char)v8)
    {
        *((char *)&v2) = v18 >> 24;
        *((char *)&v2 + 1) = v17 >> 16;
        *((char *)&v2 + 2) = v17 >> 8;
        *((char *)&v2 + 3) = v17;
        v18 = v2;
    }
    *((unsigned int *)&ptr[4]) = v18;
    if (v17 > a2)
    {
        sub_143632a50(idx, v8 & 0xff, 0, idx);
        v19 = idx->field_10;
        if ((char)v8)
        {
            v5 = v19;
            v2 = v19 >> 24;
            v3 = v19 >> 16;
            v4 = v19 >> 8;
        }
        v20 = idx->field_a;
        if ((char)v8)
        {
            v2 = _INSERT(CONCAT(v2, 0), 3, v20);
            *((char *)&v2) = v20 >> 24;
            *((char *)&v2 + 1) = v20 >> 16;
            *((char *)&v2 + 2) = v20 >> 8;
            v20 = v2;
        }
        if (128 < v20)
            v20 = 128;
        sub_1435dc710();
        v21 = v20 - 1;
        *((char *)&v0 + v20) = 0;
        if (v21 > 0)
        {
            v22 = 0;
            do
            {
                if (!*((char *)&v0 + v22))
                    *((char *)&v0 + v22) = 44;
            } while ((v22 = (unsigned long)(v22 + 1), v22 < (long long)(int)v21));
        }
    }
    *(a1) = ptr;
    return v17;
}

// ---- 0x143632b10
typedef struct st_143632b10_0 {
    char field_0;
    char field_1;
    char padding_2[2];
    int field_4;
    int field_8;
    char padding_c[4];
    char field_10;
} st_143632b10_0;

long long sub_143632b10(void* index, char a1, long long a2, long long a3, char a4, char a5, char a6, char a7)
{
    long long v8;  // r13
    unsigned long v9;  // r14
    unsigned long v18;  // rax
    unsigned long v20;  // rax
    unsigned long v21;  // rax
    unsigned long v22;  // rcx
    void* idx;  // rcx
    st_143632b10_0 *v24;  // r15
    st_143632b10_0 *iter;  // rbx
    long long v26;  // rdx
    unsigned int i;  // edx
    char v10;  // 4098
    char v28;  // cl
    unsigned int j;  // r12d
    unsigned long long v30;  // r15
    unsigned long v31;  // rax
    void* idx1;  // rbx
    char v33;  // cl
    char v34;  // cl
    unsigned long v35;  // rax
    unsigned long v37;  // rax
    unsigned long long v11;  // rbx
    unsigned long long v12;  // r15
    unsigned int v13;  // ebx
    unsigned long v14;  // rax
    unsigned long long v15;  // rdx
    unsigned long v16;  // rax
    unsigned short *v17;  // rbx
    long long v0;  // [bp-0x58]
    long long v1;  // [bp-0x50]
    long long v2;  // [bp-0x48]
    long long v3;  // [bp-0x40]
    long long v4;  // [bp-0x38]
    unsigned int v5;  // [bp+0x8]
    unsigned long long v6;  // [bp+0x10]
    unsigned long long v7;  // [bp+0x18]

    v8 = a3;
    v9 = a1;
    if (a5)
    {
        v10 = (char)index[48];
        *((char *)&index[48]) = 0;
        v9 = _INSERT(v9, 0, v10);
    }
    v6 = v11;
    v7 = v12;
    sub_143633050();
    if ((short)index[8])
    {
        v13 = 0;
        if (0 < (short)index[8])
        {
            do
            {
                v14 = (int)index[20];
                v15 = a2 + v14;
                if (!(unsigned int)v14)
                    v15 = 0;
            } while ((sub_143632b10(v15 + (long long)(int)v13 * 72, v9 & 0xff, a2, v8, a4, 0, a6, a7), v13 += 1, v13 < (int)(short)index[8]));
        }
    }
    v16 = (int)index[40];
    if ((unsigned int)v16)
    {
        v17 = a2 + v16;
        if ((char)v9)
            sub_143636010(v17, v9 & 0xff, a2, v8);
        if (*(v17) <= 4)
            *((int *)&index[40]) = 0;
    }
    v18 = (int)index[32];
    if ((unsigned int)v18 && !a7)
    {
        *((char *)&v4) = 1;
        *((char *)&v3) = a7;
        *((char *)&v2) = 1;
        *((char *)&v1) = 1;
        sub_14362f880(a2 + v18, _INSERT(0, 0, 1), v9 & 0xff, a2, v8, v1, v2, v3, v4);
        v0 = v8;
    }
    v20 = (int)index[44];
    if ((unsigned int)v20)
    {
        *((char *)&v0) = 0;
        sub_143632ea0(a2 + v20, v9 & 0xff, a2, v8, v0);
    }
    v21 = (char)index[15];
    if ((char)v21 != 1 && *((int *)index) != 4)
    {
        v22 = (int)index[36];
        if ((unsigned int)v22 && (char)v21 == 2)
        {
            if ((char)v9)
            {
                idx = v22 + a2;
                a5 = _INSERT(CONCAT(a5, 0), 0, (char)idx[3]);
                *((char *)&a5 + 1) = (char)idx[2];
                *((char *)&a5 + 2) = (char)idx[1];
                *((char *)&a5 + 3) = *((char *)idx);
                *((unsigned int *)idx) = a5;
                *((char *)&a5) = (char)idx[7];
                *((char *)&a5 + 1) = (char)idx[6];
                *((char *)&a5 + 2) = (char)idx[5];
                *((char *)&a5 + 3) = (char)idx[4];
                *((unsigned int *)&idx[4]) = a5;
                *((char *)&a5) = (char)idx[11];
                *((char *)&a5 + 1) = (char)idx[10];
                *((char *)&a5 + 2) = (char)idx[9];
                *((char *)&a5 + 3) = (char)idx[8];
                *((unsigned int *)&idx[8]) = a5;
                *((char *)&a5) = (char)idx[15];
                *((char *)&a5 + 1) = (char)idx[14];
                *((char *)&a5 + 2) = (char)idx[13];
                (&a5)[3] = (char)idx[12];
                v21 = a5;
                *((unsigned int *)&idx[12]) = v21;
                v22 = (int)index[36];
            }
            v24 = (int)v22 + a2;
            iter = &(&v24->field_0)[v24->field_8];
            if (!a7)
            {
                *((char *)&v4) = 1;
                *((char *)&v3) = a7;
                *((char *)&v2) = 1;
                v26 = _INSERT(0, 0, 1);
                *((char *)&v1) = 1;
                v21 = sub_14362f880(&(&v24->field_0)[v24->field_4], v26, v9 & 0xff, a2, v8, v1, v2, v3, v4);
            }
            if ((char)v9)
            {
                i = 0;
                if (v24->field_10 > 0)
                {
                    do
                    {
                        i += 1;
                        v28 = iter->field_0;
                        iter->field_0 = iter->field_1;
                        iter->field_1 = v28;
                        iter = iter->padding_2;
                        v21 = v24->field_10;
                    } while (i < (unsigned int)v21);
                }
            }
        }
    }
    else
    {
        *((char *)&index[15]) = 0;
        *((unsigned int *)&index[36]) = 0;
    }
    j = 0;
    if ((char)index[12] <= 0)
        return v21;
    v30 = 0;
    do
    {
        v31 = (int)index[24];
        idx1 = v30 + (!(unsigned int)v31 ? 0 : v31 + a2);
        if ((char)v9)
        {
            sub_1436332d0(idx1);
            v33 = (char)idx1[72];
            *((char *)&idx1[72]) = (char)idx1[73];
            *((char *)&idx1[73]) = v33;
            v34 = (char)idx1[74];
            *((char *)&idx1[74]) = (char)idx1[75];
            *((char *)&idx1[75]) = v34;
            *((char *)&a5) = (char)idx1[67];
            *((char *)&a5 + 1) = (char)idx1[66];
            *((char *)&a5 + 2) = (char)idx1[65];
            (&a5)[3] = (char)idx1[64];
            *((unsigned int *)&idx1[64]) = a5;
            *((char *)&v5) = (char)idx1[71];
            *((char *)&v5 + 1) = (char)idx1[70];
            *((char *)&v5 + 2) = (char)idx1[69];
            *((char *)&v5 + 3) = (char)idx1[0x44];
            *((unsigned int *)&idx1[0x44]) = v5;
        }
        v35 = (int)idx1[0x44];
        if ((unsigned int)v35 && !(char)idx1[77] && !a7)
        {
            *((char *)&v4) = 1;
            *((char *)&v3) = 0;
            *((char *)&v2) = 1;
            *((char *)&v1) = 0;
            sub_14362f880(a2 + v35, _INSERT(0, 0, 1), v9 & 0xff, a2, v8, v1, v2, v3, v4);
        }
        v37 = (char)index[12];
        j += 1;
        v30 += 80;
    } while (j < (unsigned int)v37);
    return v37;
}

