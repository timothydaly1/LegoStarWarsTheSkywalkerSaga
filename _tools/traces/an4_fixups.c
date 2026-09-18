ERROR    | 2026-09-17 06:27:20,668 | angr.state_plugins.unicorn_engine | failed loading "unicornlib.dylib", unicorn support disabled ('NoneType' object has no attribute 'unicorn_py3')
// ---- 0x14362f880
typedef struct st_14362f880_0 {
    char padding_0[18];
    char field_12;
} st_14362f880_0;

extern char g_140000000;
extern unsigned int g_145f841c4;

void* sub_14362f880(void* idx, char a1, char a2, unsigned long long a3, long long a4, char a5, unsigned long a6, char a7, char a8)
{
    unsigned long long v13;  // rbx
    void* v14;  // rcx
    unsigned long v23;  // rcx
    void* v24;  // r8
    unsigned long v25;  // rcx
    void* v26;  // r10
    unsigned long v27;  // rcx
    void* v28;  // r14
    unsigned long v29;  // rcx
    void* v30;  // rax
    unsigned long v31;  // rcx
    void* v32;  // r9
    unsigned long long v15;  // rdi
    unsigned long v33;  // rcx
    void* v34;  // rdx
    unsigned long long v35;  // r12
    unsigned int v36;  // r15d
    unsigned int v37;  // r12d
    unsigned int v38;  // edi
    unsigned int v39;  // edx
    unsigned int v40;  // edx
    unsigned long v41;  // r9
    void* v42;  // rdx
    char v16;  // al
    unsigned long i;  // r9
    void* v44;  // rdx
    unsigned long v45;  // r9
    unsigned int v46;  // r11d
    unsigned int v47;  // ecx
    unsigned int j;  // r9d
    char *iter;  // r8
    char v50;  // dl
    unsigned long long v51;  // rdx
    int v52;  // ecx
    unsigned long long v17;  // r13
    unsigned long v53;  // r8
    void* v54;  // rdx
    unsigned long k;  // r8
    void* v56;  // rdx
    unsigned long v57;  // r8
    unsigned int v58;  // ecx
    void* idx1;  // r8
    char v60;  // dl
    unsigned int v61;  // r12d
    char v62;  // r15b
    void* index;  // rbx
    unsigned long v63;  // rdx
    char v64;  // dl
    unsigned long v65;  // r11
    unsigned long v66;  // r11
    unsigned long v67;  // r9
    unsigned short *v68;  // r8
    unsigned long n;  // r9
    unsigned short *v70;  // r8
    int v71;  // ecx
    unsigned long v72;  // rax
    unsigned long long v19;  // r14
    int v73;  // ebx
    int *v74;  // rdi
    st_14362f880_0 *v75;  // rcx
    unsigned long long v20;  // r15
    char v21;  // dil
    void* v22;  // r13
    char v0;  // [bp-0x88]
    char v1;  // [bp-0x80]
    long long v2;  // [bp-0x78]
    unsigned int v3;  // [bp-0x58]
    unsigned int v4;  // [bp-0x54]
    unsigned int v5;  // [bp-0x44]
    unsigned long long v6;  // [bp-0x38]
    unsigned long long v7;  // [bp-0x30]
    unsigned long long v8;  // [bp-0x28]
    unsigned long long v9;  // [bp-0x20]
    unsigned long long v10;  // [bp-0x18]
    unsigned long long v12;  // [bp+0x20]

    g_145f841c4 = g_145f841c4 + 1;
    if (!idx)
        return NULL;
    v12 = v13;
    v14 = (!a3 ? NULL : idx);
    v10 = v15;
    v16 = (char)idx[18] & 231 | 2;
    v8 = v17;
    index = NULL;
    v7 = v19;
    v6 = v20;
    *((unsigned int *)&idx[56]) = 0;
    *((char *)&idx[18]) = v16;
    if (!v14 || a8)
    {
        v21 = a7;
        if (!v21)
            goto LABEL_14362f912;
    }
    else
    {
        v21 = a7;
    }
    *((char *)&idx[18]) = v16 | 1;
LABEL_14362f912:
    v22 = NULL;
    v1 = a8;
    v5 = *((int *)idx) & 0xffffff;
    v0 = v21;
    if (!v21)
        v22 = v14;
    sub_14362f500();
    v23 = (int)idx[36];
    v24 = index;
    if ((unsigned int)v23)
        v24 = v23 + v22;
    v25 = (int)idx[40];
    v26 = index;
    if ((unsigned int)v25)
        v26 = v25 + v22;
    v27 = (int)idx[44];
    v28 = index;
    if ((unsigned int)v27)
        v28 = v27 + v22;
    v29 = (int)idx[48];
    v30 = index;
    if ((unsigned int)v29)
        v30 = v29 + v22;
    v31 = (int)idx[52];
    v32 = index;
    if ((unsigned int)v31)
        v32 = v31 + v22;
    v33 = (int)idx[56];
    v34 = index;
    if ((unsigned int)v33)
        v34 = v33 + v22;
    v9 = v35;
    if (v5 == 4804161)
    {
        v36 = (short)idx[4];
        v37 = (short)idx[12];
        v38 = (short)idx[6] + 7 >> 2;
        if (v24)
        {
            if (v30)
            {
                v39 = v30 - v24;
            }
            else if (v34)
            {
                v39 = v34 - v24;
            }
            else
            {
                v39 = 0;
                if (v32)
                    v39 = v32 - v24;
            }
            v40 = v39 >> 3;
            v41 = v40;
            if (v40 > 0)
            {
                v42 = v24 + 6;
                do
                {
                    i = v41;
                    v44 = v42 + 8;
                    *((char *)&v3) = (char)v42[1];
                    *((char *)&v3 + 1) = *((char *)v44 - 8);
                    *((char *)&v3 + 2) = *((char *)v44 - 9);
                    *((char *)&v3 + 3) = *((char *)v44 - 10);
                    *((unsigned int *)((char *)v44 - 10)) = v3;
                    *((char *)&v4) = *((char *)v44 - 11);
                    *((char *)&v4 + 1) = *((char *)v44 - 12);
                    *((char *)&v4 + 2) = *((char *)v44 - 13);
                    *((char *)&v4 + 3) = *((char *)v44 - 14);
                    *((unsigned int *)((char *)v44 - 14)) = v4;
                    v45 = i - 1;
                    v42 = v44;
                    v41 = v45;
                } while (i != 1);
            }
        }
        v46 = v28 - v26;
        if ((char)idx[19] & 16)
        {
            v47 = (char)idx[0x11];
            j = 0;
            if ((char)v47)
            {
                iter = v26;
                do
                {
                    j += 1;
                    v50 = *(iter);
                    *(iter) = iter[1];
                    iter[1] = v50;
                    iter += 2;
                    v47 = (char)idx[0x11];
                } while (j < v47);
            }
            v51 = (v47 & 0xff) * 2;
            v52 = v46 - v51 >> 2;
            v53 = v52;
            if (v52 > 0)
            {
                v54 = (v26 + 3 + v51 & 0xfffffffffffffffc) + 2;
                do
                {
                    k = v53;
                    v56 = v54 + 4;
                    *((char *)&v4) = (char)v54[1];
                    *((char *)&v4 + 1) = *((char *)v56 - 4);
                    *((char *)&v4 + 2) = *((char *)v56 - 5);
                    *((char *)&v4 + 3) = *((char *)v56 - 6);
                    *((unsigned int *)((char *)v56 - 6)) = v4;
                    v57 = k - 1;
                    v53 = v57;
                    v54 = v56;
                } while (k != 1);
            }
        }
        else
        {
            v58 = v46 >> 1;
            if (v58 > 0)
            {
                idx1 = index;
                do
                {
                    v60 = *((char *)v26 + 0x2 * idx1);
                    *((char *)v26 + 0x2 * idx1) = *((char *)v26 + 0x2 * idx1 + 1);
                    *((char *)v26 + 0x2 * idx1 + 1) = v60;
                    idx1 += 1;
                } while (idx1 < v58);
            }
        }
        v61 = v36 * v37;
        v62 = (char)idx[19];
        v63 = v61;
        if (v62 & 2)
            v63 += (short)idx[6];
        if ((unsigned int)v63 > 0)
        {
            do
            {
                v64 = *((char *)v28 + 0x2 * index);
                *((char *)v28 + 0x2 * index) = *((char *)v28 + 0x2 * index + 1);
                *((char *)v28 + 0x2 * index + 1) = v64;
                index += 1;
            } while (index < (int)v63);
            v62 = (char)idx[19];
        }
        if (v38)
        {
            v65 = v38;
            do
            {
                v66 = v65;
                if (v61 > 0)
                {
                    v67 = v61;
                    v68 = v28;
                    do
                    {
                        n = v67;
                        v70 = v68 + 1;
                        v71 = (!(v62 & 32) ? *(v68) : *(v68) & 0x7fff);
                        if ((!(v62 & 32) ? *(v68) : *(v68) & 0x7fff) - 2 <= 9)
                            goto *((void *)((unsigned long long)&(&g_140000000)[*((int *)&(&g_140000000)[56819136 + 4 * v71])]));
                        v67 = n - 1;
                        v68 = v70;
                    } while (n != 1);
                }
            } while ((v65 = (unsigned long)(v66 - 1), v66 != 1));
        }
        v21 = a7;
        if (v5 == 4804161)
            goto LABEL_14362fd0c;
    }
    if (!v22 && !v21)
        return idx;
LABEL_14362fd0c:
    if (*((int *)idx) < 1095649592)
        return idx;
    v72 = (int)idx[60];
    if (!(unsigned int)v72)
        return idx;
    v73 = 1;
    if (1 >= *((short *)(v72 + (char *)v22)))
        return idx;
    v74 = *((int *)(v72 + (char *)v22 + 4)) + 4 + v22;
    do
    {
        v75 = *(v74) + v22;
        if (!(v75->field_12 & 2))
        {
            *((char *)&v2) = 0;
            sub_14362f880(v75, a1, a2, v22, a4, a5, v2, a7, a8);
        }
    } while ((v73 = (int)(v73 + 1), v74 += 4, v73 < (int)*((short *)(v72 + (char *)v22))));
    return idx;
}

// ---- 0x143632ea0
long long sub_143632ea0(void* a0, char a1, unsigned long a2)
{
    unsigned long v5;  // rax
    unsigned long long v6;  // r14
    void* iter;  // rax
    unsigned int j;  // r9d
    char v17;  // dl
    void* node;  // r10
    unsigned int i;  // r11d
    unsigned long v9;  // rax
    void* idx;  // r8
    char v11;  // cl
    char v12;  // cl
    char v13;  // cl
    unsigned long v14;  // rax
    unsigned int v0;  // [bp-0x28]
    unsigned int v1;  // [bp-0x24]
    unsigned int v2;  // [bp+0x8]
    unsigned int v3;  // [bp+0x10]
    unsigned long long v4;  // [bp+0x18]

    if (a1)
    {
        *((char *)&v3) = (char)a0[7];
        *((char *)&v3 + 1) = (char)a0[6];
        *((char *)&v3 + 2) = (char)a0[5];
        *((char *)&v3 + 3) = (char)a0[4];
        *((unsigned int *)&a0[4]) = v3;
    }
    v5 = (int)a0[4];
    if (!(unsigned int)v5)
        return v5;
    v4 = v6;
    node = a2 + v5;
    i = 0;
    if (*((char *)a0) > 0)
    {
        do
        {
            if (a1)
            {
                *((char *)&v3) = (char)node[3];
                *((char *)&v3 + 1) = (char)node[2];
                *((char *)&v3 + 2) = (char)node[1];
                *((char *)&v3 + 3) = *((char *)node);
                *((unsigned int *)node) = v3;
            }
            v9 = *((int *)node);
            if ((unsigned int)v9)
            {
                idx = a2 + v9;
                if (a1)
                {
                    v11 = *((char *)idx);
                    *((char *)idx) = (char)idx[1];
                    *((char *)&idx[1]) = v11;
                    v12 = (char)idx[2];
                    *((char *)&idx[2]) = (char)idx[3];
                    *((char *)&idx[3]) = v12;
                    v13 = (char)idx[4];
                    *((char *)&idx[4]) = (char)idx[5];
                    *((char *)&idx[5]) = v13;
                    *((char *)&v2) = (char)idx[11];
                    *((char *)&v2 + 1) = (char)idx[10];
                    *((char *)&v2 + 2) = (char)idx[9];
                    *((char *)&v2 + 3) = (char)idx[8];
                    *((unsigned int *)&idx[8]) = v2;
                    *((char *)&v0) = (char)idx[15];
                    *((char *)&v0 + 1) = (char)idx[14];
                    *((char *)&v0 + 2) = (char)idx[13];
                    *((char *)&v0 + 3) = (char)idx[12];
                    *((unsigned int *)&idx[12]) = v0;
                    *((char *)&v1) = (char)idx[19];
                    *((char *)&v1 + 1) = (char)idx[18];
                    *((char *)&v1 + 2) = (char)idx[0x11];
                    *((char *)&v1 + 3) = (char)idx[16];
                    *((unsigned int *)&idx[16]) = v1;
                    v14 = (int)idx[8];
                    if ((unsigned int)v14)
                    {
                        iter = v14 + idx;
                        j = 0;
                        if (0 < *((short *)idx))
                        {
                            do
                            {
                                j += 1;
                                v17 = *((char *)iter);
                                *((char *)iter) = (char)iter[1];
                                *((char *)&iter[1]) = v17;
                                iter += 2;
                            } while (j < *((short *)idx));
                        }
                    }
                }
            }
            v5 = *((char *)a0);
            i += 1;
            node += 4;
        } while (i < (unsigned int)v5);
    }
    return v5;
}

// ---- 0x143636010
long long sub_143636010(void* idx, char a1, unsigned long a2, long long a3)
{
    char v6;  // r8b
    char v7;  // r8b
    int j;  // ebx
    void* v17;  // r10
    void* v18;  // r10
    char v19;  // cl
    char v20;  // cl
    char v21;  // r9b
    char v22;  // r8b
    char v23;  // r8b
    char v24;  // r8b
    char v25;  // r8b
    unsigned long v8;  // rax
    char v26;  // r8b
    char v27;  // r8b
    unsigned long v28;  // rdx
    unsigned int v30;  // edi
    void* iter;  // rbx
    char v32;  // cl
    unsigned int k;  // r8d
    void* node;  // rdx
    char v35;  // cl
    unsigned long long v9;  // rsi
    unsigned long long v10;  // r13
    void* v11;  // rsi
    unsigned long long v12;  // rbp
    unsigned long long i;  // rbp
    unsigned long v14;  // rax
    void* iter1;  // r11
    long long v0;  // [bp-0x40]
    long long v1;  // [bp-0x38]
    long long v2;  // [bp-0x30]
    unsigned long long v3;  // [bp-0x28]
    unsigned int v4;  // [bp+0x8]
    unsigned long long v5;  // [bp+0x20]

    v6 = *((char *)idx);
    *((char *)idx) = (char)idx[1];
    *((char *)&idx[1]) = v6;
    v7 = (char)idx[2];
    *((char *)&idx[2]) = (char)idx[3];
    *((char *)&idx[3]) = v7;
    *((char *)&v4) = (char)idx[19];
    *((char *)&v4 + 1) = (char)idx[18];
    *((char *)&v4 + 2) = (char)idx[0x11];
    *((char *)&v4 + 3) = (char)idx[16];
    *((unsigned int *)&idx[16]) = v4;
    *((char *)&v4) = (char)idx[7];
    *((char *)&v4 + 1) = (char)idx[6];
    *((char *)&v4 + 2) = (char)idx[5];
    *((char *)&v4 + 3) = (char)idx[4];
    *((unsigned int *)&idx[4]) = v4;
    if (*((short *)idx) <= 4)
        return v4;
    v8 = (short)idx[2];
    v5 = v9;
    v3 = v10;
    v11 = (int)idx[16] + idx;
    if (0 < (unsigned short)v8)
    {
        v12 = v8 & 0xffff;
        do
        {
            i = v12;
            sub_143635e60(v11);
            v14 = (int)v11[0x44];
            if ((unsigned int)v14)
            {
                iter1 = idx + v14;
                j = 0;
                if (0 < (short)v11[24])
                {
                    v17 = iter1 + 7;
                    do
                    {
                        iter1 += 20;
                        *((char *)&v4) = *((char *)v17 - 4);
                        v18 = v17 + 20;
                        *((char *)&v4 + 1) = *((char *)v17 - 5);
                        *((char *)&v4 + 2) = *((char *)v18 - 26);
                        *((char *)&v4 + 3) = *((char *)iter1 - 20);
                        *((unsigned int *)((char *)iter1 - 20)) = v4;
                        v19 = *((char *)v18 - 23);
                        *((char *)v18 - 23) = *((char *)v18 - 22);
                        *((char *)v18 - 22) = v19;
                        v20 = *((char *)v18 - 21);
                        *((char *)v18 - 21) = *((char *)v18 - 20);
                        *((char *)v18 - 20) = v20;
                        v21 = *((char *)v18 - 18);
                        v22 = v21 * 128;
                        v23 = (!(v21 & 2) ? v22 : v22 | 64);
                        v24 = (!(v21 & 4) ? v23 : v23 | 32);
                        v25 = (!(v21 & 8) ? v24 : v24 | 16);
                        v26 = (!(v21 & 16) ? v25 : v25 | 8);
                        v27 = (!(v21 & 32) ? v26 : v26 | 4);
                        v28 = (!(v21 & 64) ? v27 : v27 | 2);
                        j += 1;
                        *((char *)v18 - 18) = (v21 >= 0 ? (char)v28 : (char)v28 | 1);
                        v17 = v18;
                    } while (j < (short)v11[24]);
                }
            }
            v8 = (int)v11[72];
            if ((unsigned int)v8)
            {
                *((char *)&v2) = 0;
                *((char *)&v1) = 1;
                *((char *)&v0) = 0;
                v8 = sub_14362f830(idx + v8, _INSERT(v28, 0, 1), a1, idx + v8, a3, v0, v1, v2);
            }
            if ((short)v11[22] > 0)
            {
                v30 = 0;
                iter = (int)v11[80] + idx;
                do
                {
                    if ((char)sub_14021c0a0(v30))
                    {
                        v32 = *((char *)iter);
                        v8 = (char)iter[1];
                        *((char *)iter) = v8;
                        *((char *)&iter[1]) = v32;
                    }
                } while ((v30 += 1, iter += 2, v30 < 29));
                if ((short)v11[22] > 0)
                {
                    k = 0;
                    node = (int)v11[76] + idx;
                    do
                    {
                        k += 1;
                        v35 = *((char *)node);
                        *((char *)node) = (char)node[1];
                        *((char *)&node[1]) = v35;
                        node += 2;
                        v8 = (short)v11[22];
                    } while (k < (unsigned int)v8);
                }
            }
            v11 += 120;
            v12 = i - 1;
        } while (i != 1);
    }
    return v8;
}

