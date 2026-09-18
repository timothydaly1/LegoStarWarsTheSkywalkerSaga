ERROR    | 2026-09-17 06:30:31,047 | angr.state_plugins.unicorn_engine | failed loading "unicornlib.dylib", unicorn support disabled ('NoneType' object has no attribute 'unicorn_py3')
// ---- 0x14362b9e0
typedef struct st_14362b9e0_1 {
    unsigned short field_0;
} st_14362b9e0_1;

typedef struct st_14362b9e0_0 {
    char padding_0[8];
    unsigned long long field_8;
    struct st_14362b9e0_1 *field_10;
} st_14362b9e0_0;

typedef struct st_14362b9e0_2 {
    char padding_0[4];
    unsigned short field_4;
    unsigned short field_6;
    unsigned short field_8;
    char padding_a[2];
    unsigned short field_c;
    char padding_e[2];
    char field_10;
    char field_11;
    char field_12;
    char field_13;
    char padding_14[8];
    unsigned int field_1c;
    unsigned int field_20;
    char padding_24[4];
    struct st_14362b9e0_0 *field_28;
    int field_2c;
} st_14362b9e0_2;

extern char g_140000000;
extern char g_145f840d0;

char * sub_14362b9e0(st_14362b9e0_2 *idx, unsigned long a1, unsigned int *a2, unsigned int a3)
{
    unsigned int v29;  // ebx
    unsigned long long v30;  // r11
    unsigned long v39;  // rcx
    char v40;  // r10b
    char *iter;  // rbx
    unsigned long v42;  // r9
    unsigned long v43;  // rdx
    char v44;  // r8b
    unsigned long j;  // rdx
    unsigned short v46;  // ax
    unsigned short *v47;  // rsi
    char *v48;  // rax
    unsigned long v31;  // r13
    unsigned int i;  // r9d
    char v50;  // r10b
    char *v51;  // r8
    uint128_t v52;  // xmm8
    unsigned int v53;  // r13d
    unsigned long v54;  // rdx
    unsigned int v55;  // ecx
    unsigned int v56;  // r8d
    unsigned long index;  // rcx
    int v58;  // xmm0
    unsigned int *iter1;  // r12
    unsigned long long idx1;  // rax
    unsigned int v60;  // zmm0
    int v61;  // xmm4
    int v62;  // xmm5
    int v63;  // xmm6
    int v64;  // xmm1
    int v65;  // xmm2
    int v66;  // xmm1
    uint128_t v68;  // 5188
    unsigned int v33;  // r8d
    uint128_t v69;  // 5190
    uint128_t v70;  // 5192
    uint128_t v71;  // 5194
    unsigned long long idx2;  // rax
    unsigned long long v34;  // rsi
    unsigned long long v35;  // rdi
    unsigned int v36;  // zmm10
    unsigned long long v37;  // r14
    unsigned short *node;  // rsi
    unsigned int v0;  // [bp-0x128]
    unsigned int v1;  // [bp-0x124]
    unsigned int v2;  // [bp-0x120]
    char *v3;  // [bp-0x118]
    unsigned int v4;  // [bp-0x110]
    char v5;  // [bp-0x108]
    char v6;  // [bp-0xf8]
    unsigned long v7;  // [bp-0xe8]
    unsigned long long v8;  // [bp-0xe0]
    unsigned int v9;  // [bp-0xd8]
    unsigned int v10;  // [bp-0xd4]
    unsigned int v11;  // [bp-0xd0]
    unsigned int v12;  // [bp-0xcc]
    unsigned int v13;  // [bp-0xc8]
    unsigned int v14;  // [bp-0xc4]
    unsigned long long v15;  // [bp-0xc0]
    unsigned int v16;  // [bp-0xb8]
    unsigned int v17;  // [bp-0xb4]
    unsigned int v18;  // [bp-0xb0]
    unsigned int v19;  // [bp-0xac]
    uint128_t v20;  // [bp-0x68]
    unsigned long long v21;  // [bp-0x38]
    unsigned long long v22;  // [bp-0x30]
    char v23;  // [bp+0x0]
    char v24;  // [bp+0x8]
    unsigned long long v25;  // [bp+0x10]
    char v26;  // [bp+0x20]
    char *v27;  // [bp+0x28]
    unsigned int v28;  // [bp+0x30]

    v29 = idx->field_4;
    v30 = 0;
    v31 = a3;
    iter1 = a2;
    v33 = idx->field_c;
    v4 = v33;
    v8 = 0;
    if (a3 >= v29)
        return &v23;
    v25 = v34;
    v22 = v35;
    if (g_145f840d0 && idx->field_10)
    {
        v36 = ConvI32StoF32x4(idx->field_6 - 4 + idx->field_10);
    }
    else
    {
        sub_14362cbf0();
        v30 = v8;
        v33 = v4;
    }
    v21 = v37;
    if (idx->field_12 & 4)
    {
        node = &idx->field_28->field_10->field_0;
        v39 = idx->field_28->field_8;
    }
    else
    {
        node = *((int *)((char *)&idx->field_28 + 4));
        v7 = (int)idx->field_28;
        if (idx->field_12 & 1)
            goto LABEL_14362bab5;
        node += idx;
        v39 = &idx->padding_0[v7];
    }
    v7 = v39;
LABEL_14362bab5:
    v40 = idx->field_13;
    v2 = idx->field_8;
    v1 = v36 & 3;
    iter = &node[v33 * v29];
    v15 = v7 + idx->field_11 * 2;
    if (v40 & 16)
    {
        v30 = (v15 + 3 & 0xfffffffffffffffc) - 64;
        v8 = v30;
        if (v40 & 2)
            iter = &iter[2 * idx->field_6];
    }
    v13 = 0x7fff;
    if ((unsigned int)v31 > 0)
    {
        do
        {
            v42 = v31;
            if (v33)
            {
                v43 = v4;
                v44 = v40;
                do
                {
                    j = v43;
                    v46 = *(node);
                    v47 = node + 1;
                    if (v44 & 32)
                        v46 = *(node) & 0x7fff;
                    if (!(v44 & 32))
                        iter += 1;
                    v43 = j - 1;
                    node = v47;
                } while (j != 1);
                v33 = v4;
                node = v47;
            }
        } while ((v31 = (unsigned long)(v42 - 1), v42 != 1));
        v30 = v8;
    }
    v48 = (char *)_INSERT(0, 0, 0);
    i = 0;
    v26 = 0;
    v0 = 0;
    if (v33)
    {
        v48 = v28;
        v50 = v40 & 32;
        v51 = v27;
        v20 = v52;
        v53 = -((unsigned int)v48);
        v24 = v40 & 32;
        v3 = v51;
        do
        {
            v54 = *(node);
            node += 1;
            if (v50)
            {
                v55 = (unsigned int)v54 & 0xffff & 0x8000;
                v54 = _INSERT(v54, 0, (unsigned short)v54 & (unsigned short)v13);
            }
            else
            {
                v55 = *(iter) & 1;
                iter += 1;
            }
            if (v51)
            {
                if (i == *(v51))
                {
                    v48 = v28;
                    v3 = v51 + 1;
                }
                else if (((unsigned int)v54 & 0xffff) - 2 <= 9)
                {
                    goto *((void *)((unsigned long long)&(&g_140000000)[*((int *)&(&g_140000000)[56803836 + 4 * ((unsigned int)v54 & 0xffff)])]));
                }
            }
            if ((unsigned int)v48 >= 0 && (v14 = v53, v53 <= 2))
            {
                v56 = (unsigned int)v54 & 0xffff;
                if (v56 - 2 <= 13)
                    goto *((void *)((unsigned long long)&(&g_140000000)[*((int *)&(&g_140000000)[56803876 + 4 * v56])]));
                index = v53;
                if (v50)
                {
                    v58 = (int)v56;
                }
                else
                {
                    idx1 = v54 & 0xffff;
                    if (v30)
                    {
                        v60 = *((int *)(v30 + idx1 * 4));
                        goto LABEL_14362bf20;
                    }
                    else
                    {
                        v58 = (int)*((short *)(v15 + idx1 * 2 - 32));
                    }
                }
                v60 = AddV(MulV(ConvI32StoF32x4(v58), idx->field_20), idx->field_1c);
LABEL_14362bf20:
                *((unsigned int *)&(&v5)[4 * index]) = v60;
                *((unsigned int *)&(&v6)[4 * index]) = v60;
                if (v14 == 2 && !v26)
                {
                    sub_1436214a0(&v16);
                    sub_1436214a0(&v9);
                    v61 = (int)v10;
                    v62 = (int)v9;
                    v63 = (int)v11;
                    v64 = MulV(v63, v18);
                    v65 = AddV(MulV(v61, v17), MulV(v62, v16));
                    v66 = (int)v12;
                    if (!(CmpF(0, *((unsigned int *)&AddV(AddV(v65, v64), MulV(v66, v19)))) & 1 | (CmpF(0, *((unsigned int *)&AddV(AddV(v65, v64), MulV(v66, v19)))) & 69) >> 6 & 1))
                    {
                        v68 = fnegf(v62);
                        v9 = v68;
                        v69 = fnegf(v61);
                        v10 = v69;
                        v70 = fnegf(v63);
                        v11 = v70;
                        v71 = fnegf(v66);
                        v12 = v71;
                    }
                    sub_1436218b0((char *)iter1 - 8, &v16, &v9);
                    iter1 += 1;
                    i = v0;
                    goto LABEL_14362c06b;
                }
            }
            else
            {
                v51 = v54 & 0xffff;
                if ((unsigned int)(v51 - 6) <= 9)
                    goto *((void *)((unsigned long long)&(&g_140000000)[*((int *)&(&g_140000000)[56803940 + 4 * (unsigned int)(v51 - 6)])]));
                if (v50)
                {
                    *(iter1) = AddV(MulV((unsigned int)v51, idx->field_20), idx->field_1c);
LABEL_14362c06b:
                    v51 = v3;
                    continue;
                }
                else
                {
                    __unsupported_jumpkind_Ijk_NoDecode()
                    idx2 = v54 & 0xffff;
                    if (v30)
                        *(iter1) = *((int *)(v30 + idx2 * 4));
                    else
                        *(iter1) = AddV(MulV(*((short *)(v15 + idx2 * 2 - 32)), idx->field_20), idx->field_1c);
                }
            }
            i += 1;
            v53 += 1;
            v48 = v28;
            iter1 += 1;
            v0 = i;
            v30 = v8;
            v50 = v24;
        } while (i < v4);
    }
    return v48;
}
ERROR    | 2026-09-17 06:31:56,242 | angr.analyses.decompiler.structured_codegen.c | Store data lifted to a C type of a different size: unsigned int (32 bits) is 32 bits, the store is 128 bits. Using the store width.

// ---- 0x14362d590
typedef struct st_14362d590_4 {
    char padding_0[125];
    char field_7d;
    char padding_7e[2];
    unsigned long long field_80;
    char padding_88[40];
    unsigned long long field_b0;
    char padding_b8[40];
    struct st_14362d590_5 *field_e0;
    unsigned long long field_e8;
} st_14362d590_4;

typedef struct st_14362d590_0 {
    unsigned int field_0;
    unsigned int field_4;
    unsigned int field_8;
    unsigned int field_c;
    unsigned int field_10;
    unsigned int field_14;
    char field_18;
    char padding_19[7];
    char field_20;
} st_14362d590_0;

typedef struct st_14362d590_2 {
    struct st_14362d590_0 *field_0;
    unsigned long long field_8;
    struct st_14362d590_1 *field_10;
    unsigned long long field_18;
    unsigned long long field_20;
} st_14362d590_2;

typedef struct st_14362d590_3 {
    char padding_0[4];
    char field_4;
    char padding_5[3];
    unsigned short field_8;
    char padding_a[8];
    char field_12;
    char field_13;
    char padding_14[16];
    int field_24;
    struct st_14362d590_2 *field_28;
    int field_2c;
    int field_30;
    int field_34;
} st_14362d590_3;

typedef struct st_14362d590_1 {
    unsigned short field_0;
    unsigned short field_2;
    unsigned short field_4;
    char field_6;
} st_14362d590_1;

typedef struct st_14362d590_5 {
    unsigned long long field_0;
} st_14362d590_5;

extern char g_14446b934;
extern char g_14446b9d0;
extern char g_14446b9e0;
extern uint128_t g_145f80180;
extern uint128_t g_145f84100;

unsigned long long sub_14362d590(unsigned long long a0, unsigned long long a1, unsigned long a2, unsigned long a3, long long a4, long long a5, unsigned long a6)
{
    unsigned long long v7;  // rsi
    unsigned long long v8;  // rdi
    uint128_t v17;  // xmm11
    long long v103;  // rbx
    unsigned int v104;  // r8d
    unsigned int v105;  // ecx
    unsigned int v106;  // edx
    unsigned int v107;  // r10d
    unsigned int v108;  // r9d
    char v109;  // cl
    unsigned int v110;  // ecx
    unsigned long v111;  // rcx
    uint128_t v18;  // xmm12
    unsigned int v112;  // zmm1
    unsigned int v113;  // zmm3
    unsigned int v114;  // zmm0
    int v115;  // xmm4
    int v116;  // xmm12
    int v117;  // xmm13
    unsigned int v118;  // zmm0
    uint128_t v119;  // xmm1
    uint128_t v120;  // xmm10
    unsigned int v121;  // zmm5
    int v19;  // xmm13
    unsigned int v122;  // zmm11
    uint128_t v123;  // xmm9
    unsigned int v124;  // zmm5
    int v125;  // xmm10
    uint128_t v126;  // xmm0
    uint128_t v127;  // xmm1
    unsigned int v128;  // zmm2
    unsigned int v129;  // zmm3
    unsigned int v130;  // zmm0
    uint128_t v131;  // xmm13
    int v20;  // xmm14
    int v132;  // xmm13
    int v133;  // xmm12
    int v134;  // xmm14
    unsigned int v135;  // zmm0
    uint128_t v136;  // xmm1
    uint128_t v137;  // xmm10
    unsigned int v138;  // zmm5
    unsigned int v139;  // zmm11
    unsigned int v140;  // zmm5
    uint128_t v141;  // xmm9
    int v21;  // xmm15
    int v142;  // xmm10
    uint128_t v143;  // xmm2
    int v144;  // xmm0
    uint128_t v145;  // xmm1
    uint128_t v146;  // xmm14
    int v147;  // xmm11
    int v148;  // xmm13
    unsigned int v149;  // zmm0
    unsigned int v150;  // zmm1
    unsigned int v151;  // zmm9
    unsigned long long idx;  // rbp
    unsigned int v152;  // zmm5
    unsigned int v153;  // zmm8
    unsigned int v154;  // zmm10
    unsigned int v155;  // zmm5
    int v156;  // xmm9
    uint128_t v157;  // xmm8
    unsigned int v158;  // zmm3
    int v159;  // xmm13
    uint128_t v160;  // xmm5
    uint128_t v161;  // xmm13
    st_14362d590_3 *idx1;  // rcx
    unsigned int v162;  // zmm2
    int v164;  // xmm1
    unsigned int v165;  // zmm1
    unsigned int v166;  // zmm2
    unsigned int v167;  // zmm3
    unsigned int v168;  // zmm1
    int v169;  // xmm7
    char v170;  // al
    unsigned int v24;  // r12d
    unsigned long long v171;  // rbx
    unsigned long v172;  // rdx
    unsigned long long v173;  // rcx
    unsigned long long idx2;  // rax
    st_14362d590_4 *index;  // r13
    long long v25;  // rsi
    int v176;  // xmm5
    unsigned long long *v177;  // r10
    unsigned long v178;  // 4176
    unsigned long v179;  // rdx
    int v180;  // xmm0
    uint128_t v181;  // xmm4
    int v182;  // xmm5
    uint128_t v183;  // xmm8
    unsigned long long v184;  // rax
    int v185;  // xmm1
    unsigned long long v26;  // r14
    unsigned int v186;  // zmm2
    int v187;  // xmm2
    uint128_t v188;  // xmm0
    unsigned long long v189;  // rax
    unsigned long long v9;  // r12
    unsigned int v27;  // zmm3
    int v28;  // xmm9
    int v29;  // xmm2
    unsigned int v30;  // edi
    unsigned int v31;  // zmm6
    unsigned int v32;  // ecx
    char v33;  // cl
    unsigned long v34;  // rax
    unsigned long node;  // r12
    unsigned long iter;  // rsi
    unsigned long long v10;  // r13
    unsigned long v37;  // r8
    unsigned long v38;  // r9
    unsigned long v39;  // r10
    char v40;  // r14b
    unsigned long v41;  // r15
    unsigned long long v42;  // rbx
    unsigned long long v43;  // r13
    void* iter1;  // rdi
    unsigned long long i;  // r13
    unsigned long long v46;  // rax
    unsigned long long v11;  // r14
    unsigned long long v47;  // rbx
    unsigned long v48;  // r11
    unsigned long long v49;  // r10
    uint128_t v50;  // xmm1
    int v51;  // xmm7
    int v52;  // xmm14
    uint128_t v53;  // xmm12
    unsigned int v54;  // eax
    uint128_t v55;  // xmm11
    int v56;  // xmm15
    int v12;  // xmm6
    int v57;  // xmm0
    int v58;  // xmm0
    uint128_t v59;  // xmm4
    uint128_t v60;  // xmm3
    uint128_t v61;  // xmm13
    unsigned long long v62;  // rax
    unsigned int v63;  // r8d
    unsigned long long v64;  // r13
    unsigned int v65;  // r9d
    unsigned long v66;  // rbx
    int v13;  // xmm7
    long long v67;  // rcx
    unsigned long long v68;  // rcx
    unsigned long long v69;  // rax
    long long j;  // rbx
    char v71;  // cl
    unsigned short v72;  // dx
    unsigned short v73;  // r8w
    unsigned short v74;  // ax
    unsigned short v75;  // cx
    int v14;  // xmm8
    unsigned int iter2;  // r14d
    unsigned long long v77;  // r9
    unsigned long long v78;  // r8
    unsigned long long v79;  // rdx
    void* v80;  // rcx
    int v81;  // xmm8
    int v82;  // xmm10
    int v15;  // xmm9
    int v83;  // xmm4
    unsigned long v84;  // rsi
    uint128_t v85;  // xmm2
    uint128_t v86;  // xmm1
    uint128_t v87;  // xmm0
    uint128_t v88;  // xmm5
    uint128_t v89;  // xmm9
    uint128_t v90;  // xmm3
    unsigned long long v91;  // r8
    unsigned long long v92;  // r12
    int v16;  // xmm10
    unsigned long long v93;  // r13
    unsigned long long v94;  // rbx
    unsigned long long k;  // r8
    unsigned long v96;  // rdx
    unsigned int v97;  // ecx
    unsigned int v98;  // ecx
    unsigned int v99;  // ecx
    unsigned int v100;  // ecx
    unsigned int v101;  // zmm0
    unsigned int v102;  // ecx
    unsigned long long v0;  // [bp-0x30]
    unsigned long long v1;  // [bp-0x28]
    unsigned long long v2;  // [bp-0x20]
    unsigned long long v3;  // [bp-0x18]
    unsigned long long v4;  // [bp-0x10]
    unsigned long long v5;  // [bp+0x8]
    unsigned long long v6;  // [bp+0x10]

    v6 = a1;
    v5 = a0;
    v4 = v7;
    v3 = v8;
    v2 = v9;
    v1 = v10;
    v0 = v11;
    rsp = (int)(int *)((char *)&r15 - sub_1435da670());
    *((uint128_t *)(rsp + 5520)) = (uint128_t)v12;
    *((uint128_t *)(rsp + 5504)) = (uint128_t)v13;
    *((uint128_t *)(rsp + 5488)) = (uint128_t)v14;
    *((uint128_t *)(rsp + 5472)) = (uint128_t)v15;
    *((uint128_t *)(rsp + 5456)) = (uint128_t)v16;
    *((uint128_t *)(rsp + 5440)) = v17;
    *((uint128_t *)(rsp + 5424)) = v18;
    *((uint128_t *)(rsp + 5408)) = (uint128_t)v19;
    *((uint128_t *)(rsp + 5392)) = (uint128_t)v20;
    *((uint128_t *)(rsp + 0x1500)) = (uint128_t)v21;
    idx = rsp + 192 & 0xffffffffffffff80;
    v24 = idx1->field_4;
    v25 = *((long long *)(rsp + 5640));
    v26 = *((long long *)(rsp + 0x1600));
    v28 = (int)(CONCAT(CONCAT(v27, v27), CONCAT(v27, v27)));
    *((uint128_t *)(idx + 672)) = (uint128_t)v28;
    *((unsigned long *)(idx + 784)) = 0;
    *((unsigned int *)(idx + 712)) = v24;
    *((unsigned int *)(idx + 272)) = v24;
    v30 = *((unsigned int *)&v29);
    v31 = (unsigned int)(SubV(v29, ConvI32StoF32x4(v30)));
    *((unsigned int *)(rsp + 5616)) = v31;
    *((uint128_t *)(idx + 960)) = CONCAT(CONCAT(v31, v31), CONCAT(v31, v31));
    if (v25)
    {
        rsp = rsp - 8;
        *((unsigned long long *)(idx + 784)) = sub_143631620(v25);
        if (!v26)
        {
            v32 = *((char *)(v25 + 124));
            *((unsigned int *)(idx + 272)) = (v32 < v24 ? v32 & 0xff : v24 & 0xff);
        }
    }
    v33 = idx1->field_12;
    if (v33 & 4)
    {
        v34 = idx1->field_28;
        node = *((long long *)(v34 + 16));
        iter = *((long long *)v34);
        v37 = *((long long *)(v34 + 8));
        v38 = *((long long *)(v34 + 24));
        *((long long *)(idx + 696)) = *((long long *)(v34 + 32));
    }
    else
    {
        v39 = idx1->field_30;
        node = *((int *)((char *)&idx1->field_28 + 4));
        v37 = (int)idx1->field_28;
        iter = idx1->field_24;
        v38 = idx1->field_2c;
        *((unsigned long *)(idx + 696)) = v39;
        *((unsigned long *)(idx + 704)) = node;
        *((unsigned long *)(idx + 728)) = v37;
        if (v33 & 1)
            goto LABEL_14362d72d;
        node = &idx1->padding_0[node];
        iter = &idx1->padding_0[iter];
        *((st_14362d590_3 **)(idx + 696)) = &idx1->padding_0[v39];
        v37 = &idx1->padding_0[v37];
        v38 = &idx1->padding_0[v38];
    }
    *((unsigned long *)(idx + 728)) = v37;
    *((unsigned long *)(idx + 704)) = node;
LABEL_14362d72d:
    v40 = idx1->field_13;
    v41 = idx1->field_8;
    *((char *)idx) = v40;
    *((unsigned int *)(idx + 276)) = v30 & 3;
    *((unsigned long *)(idx + 792)) = 0;
    if (v40 & 16)
        *((unsigned long long *)(idx + 792)) = (v37 + 3 & 0xfffffffffffffffc) - 64;
    v42 = idx + 1104;
    v43 = 0xff;
    *((char *)(idx + 2)) = v40 & 32;
    iter1 = ((int)(((int)(v30) >> 31 & 3) + v30) >> 2) * (v41 & 0xffff) + v38;
    do
    {
        i = v43;
        rsp = rsp - 8;
        v46 = sub_1400acc80(v42);
        v42 += 16;
        v43 = i - 1;
    } while (i != 1);
    v47 = _INSERT(0, 0, 0);
    *((char *)(idx + 1)) = 0;
    if (*((int *)(idx + 272)) > (unsigned int)v43)
    {
        v48 = *((int *)(idx + 276));
        v49 = v48 & 0xffffffff;
        v50 = 0x3f8000003f8000003f8000003f800000;
        v51 = (int)*((int128_t *)(idx + 672));
        v52 = (int)*((int128_t *)(idx + 672));
        v53 = 1015154721;
        v54 = (unsigned int)v48 * 6;
        v55 = 0xbf800000;
        v56 = (int)*((int128_t *)(idx + 672));
        *((int128_t *)(idx + 896)) = *((int128_t *)(idx + 672));
        *((int128_t *)(idx + 880)) = *((int128_t *)(idx + 672));
        *((int128_t *)(idx + 912)) = *((int128_t *)(idx + 672));
        *((int128_t *)(idx + 928)) = *((int128_t *)(idx + 672));
        v57 = (int)*((int128_t *)(idx + 672));
        *((unsigned int *)(idx + 716)) = v54;
        *((uint128_t *)(idx + 832)) = (uint128_t)v57;
        v58 = (int)*((int128_t *)(idx + 672));
        *((unsigned int *)(idx + 720)) = v54 + 6;
        v46 = 0;
        *((uint128_t *)(idx + 944)) = (uint128_t)v58;
        *((unsigned long *)(idx + 800)) = v48;
        *((uint128_t *)(idx + 992)) = (uint128_t)0x3f8000003f8000003f8000003f800000;
        *((uint128_t *)(idx + 976)) = (uint128_t)v51;
        *((uint128_t *)(idx + 816)) = (uint128_t)v52;
        do
        {
            v59 = 0;
            v60 = v50;
            *((uint128_t *)(idx + 0x100)) = (uint128_t)0;
            v61 = v50;
            *((uint128_t *)(idx + 752)) = g_145f80180;
            *((uint128_t *)(idx + 0x300)) = v50;
            *((uint128_t *)(idx + 848)) = v50;
            if ((unsigned int)v46 >= *((int *)(idx + 712)))
                continue;
            v62 = *((long long *)(idx + 784));
            v63 = 0x100;
            v64 = v47 & 0xff;
            *((unsigned long long *)(idx + 864)) = v64;
            v65 = _INSERT(0, 0, !v62);
            *((unsigned int *)(idx + 4)) = v65;
            if (v62)
            {
                v66 = *((long long *)v62);
                v67 = *((long long *)(v62 + 8)) - v66;
                if (*((char *)(idx + 1)) < ((unsigned long long)((int128_t)(3074457345618258603 * v67) >> 0x44) + ((unsigned long long)((int128_t)(3074457345618258603 * v67) >> 0x44) >> 63) & 0xff))
                {
                    v68 = _INSERT(v67, 0, 1);
                    v69 = v64 * 96;
                    v63 = *((char *)(v69 + v66 + 92));
                    if (*((long long *)(rsp + 5648)))
                        v68 = _INSERT(v68, 0, *((char *)(*((long long *)(rsp + 5648)) + v64)));
                    v65 = (*((char *)(v69 + v66 + 93)) & 64 ? 0 : (unsigned int)v68 & 0xff);
                    *((unsigned int *)(idx + 4)) = v65;
                    goto LABEL_14362d970;
                }
            }
LABEL_14362d970:
            if (v63 < *((int *)(idx + 272)))
            {
                v61 = *((int128_t *)(idx + v63 * 16 + 1104));
                *((uint128_t *)(idx + 848)) = v61;
            }
            j = 0;
            *((unsigned long *)(idx + 808)) = 0;
            do
            {
                v71 = *((char *)(*((long long *)(idx + 696)) + v64));
                if (!(v71 & (&g_14446b934)[j]))
                {
                    if (j == 2)
                    {
                        *((uint128_t *)(idx + 0x300)) = v50;
                        if (v71 & 16)
                            *((uint128_t *)(idx + 0x300)) = v50 / v61;
                    }
                    v59 = *((int128_t *)(idx + 0x100));
                    if (v40 & 64 && j == 2)
                        continue;
                    goto LABEL_14362dc11;
                }
                v72 = *((short *)(node + 2));
                v73 = *((short *)(node + 4));
                v74 = (*((char *)(idx + 2)) ? 0x7fff : 0xffff);
                *((unsigned short *)(idx + 690)) = v72 & v74;
                v75 = v74 & *((short *)node);
                *((unsigned short *)(idx + 688)) = v75;
                *((unsigned short *)(idx + 692)) = v73 & v74;
                if (j == 1)
                {
                    if (v75 == 2)
                    {
                        if ((char)v65)
                        {
                            *((unsigned long *)(rsp + 40)) = iter;
                            *((unsigned int *)(rsp + 32)) = v31;
                            rsp = rsp - 8;
                            sub_14362ccd0(iter1, v48 & 0xffffffff, v41 & 0xffff, idx + 752, v103, a4);
                        }
                        v59 = *((int128_t *)(idx + 0x100));
                        iter1 += 16;
                        iter += 32;
                        goto LABEL_14362dc06;
                    }
                    if (v75 == 4)
                    {
                        rsp = rsp - 8;
                        sub_143614590(idx + 752, *((int *)(iter + 4)));
                        v59 = *((int128_t *)(idx + 0x100));
                        iter += 8;
                        goto LABEL_14362dc06;
                    }
                }
                *((uint128_t *)(idx + 384)) = (uint128_t)0x3f8000003f8000003f800000;
                *((uint128_t *)(idx + 0x200)) = (uint128_t)0x3f8000003f8000003f800000;
                *((uint128_t *)(idx + 128)) = (uint128_t)0;
                iter2 = 0;
                *((unsigned int *)(idx + 640)) = 1;
                *((unsigned int *)(idx + 644)) = 1;
                *((unsigned int *)(idx + 648)) = 1;
                *((unsigned int *)(idx + 280)) = 1;
                *((unsigned int *)(idx + 284)) = 1;
                *((unsigned int *)(idx + 288)) = 1;
                if (!(v75 == 6 && (v72 & v74) == v75 && (v73 & v74) == v75))
                {
                    v91 = 3;
                    v92 = idx + 688;
                    *((unsigned long *)(idx + 736)) = 3;
                    v93 = 0;
                    v94 = 0;
                    do
                    {
                        k = v91;
                        if (!(char)v65)
                            continue;
                        v96 = *((short *)v92);
                        v97 = (unsigned int)v96 & 0xffff;
                        v98 = v97 - 6;
                        if (v97 != 6)
                        {
                            v99 = v98 - 1;
                            if (v98 == 1)
                            {
                                *((unsigned int *)(rsp + 48)) = v31;
                                *((unsigned long long *)(rsp + 40)) = idx + 0x200 + v93;
                                *((unsigned long long *)(rsp + 32)) = idx + 384 + v93;
                                rsp = rsp - 8;
                                sub_14362d040(iter1, v48 & 0xffffffff, v41 & 0xffff, iter, v103, a4, a5);
                                v48 = *((int *)(idx + 276));
                                v91 = *((long long *)(idx + 736));
                                v49 = *((long long *)(idx + 800));
                                v65 = *((int *)(idx + 4));
                                goto LABEL_14362dec4;
                            }
                            v100 = v99 - 4;
                            if (v99 == 4)
                            {
                                *((int *)(idx + v94 + 384)) = *((int *)((char *)iter1 + 4 * v49));
                                if ((unsigned int)v48 == 3)
                                {
                                    *((int *)(idx + v94 + 0x200)) = *((int *)(v41 + (char *)iter1));
                                    goto LABEL_14362dec4;
                                }
                                else
                                {
                                    *((int *)(idx + v94 + 0x200)) = *((int *)((char *)iter1 + 4 * v49 + 4));
                                    goto LABEL_14362dec4;
                                }
                            }
                            if (v100 != 3)
                            {
                                if (v100 != 4)
                                {
                                    if (*((char *)idx) & 32)
                                    {
                                        *((unsigned int *)(idx + v94 + 280)) = v96;
                                        *((unsigned int *)(idx + v94 + 640)) = v96;
                                    }
                                    else
                                    {
                                        if (*((long long *)(idx + 792)))
                                        {
                                            v101 = *((int *)(*((long long *)(idx + 792)) + v96 * 4));
                                            iter2 += 1;
                                            goto LABEL_14362deb2;
                                        }
                                        else
                                        {
                                            v102 = *((short *)(*((long long *)(idx + 728)) + v96 * 2 - 32));
                                            *((unsigned int *)(idx + v94 + 280)) = v102;
                                            *((unsigned int *)(idx + v94 + 640)) = v102;
                                        }
                                    }
                                    iter2 += 1;
                                    v101 = *((int *)(*((long long *)(rsp + 5600)) + 32));
                                    *((int *)(idx + v94 + 128)) = *((int *)(*((long long *)(rsp + 5600)) + 28));
                                    goto LABEL_14362deb2;
                                }
                            }
                            else
                            {
                                *((unsigned int *)(idx + v94 + 280)) = 0;
                                *((unsigned int *)(idx + v94 + 640)) = 0;
                            }
                            iter2 += 1;
                            goto LABEL_14362dec4;
                        }
                        else
                        {
                            v104 = *((int *)(v41 + (char *)iter1));
                            v105 = *((int *)iter1) & 0xff;
                            v106 = *((int *)iter1) >> 8;
                            v107 = v104 & 0xff;
                            v108 = v107 - v105;
                            v109 = *((int *)(idx + 716));
                            *((unsigned int *)(idx + 656)) = v105 * 63;
                            v110 = *((int *)(idx + 656)) + v108 * (v106 >> (v109 & 31) & 63);
                            *((unsigned int *)(idx + v94 + 640)) = v110;
                            if ((CmpF(v31, 0) & 69) >> 2 & 1 || !(CmpF(v31, 0) & 64))
                                v110 = ((unsigned int)v48 < 3 ? *((int *)(idx + 656)) + v108 * (v106 >> ((char)*((int *)(idx + 720)) & 31) & 63) : (v104 >> 8 & 63) * (unsigned int)(*(2 * v41 + (char *)iter1) - v107) + v107 * 63);
                            v91 = *((long long *)(idx + 736));
                            v65 = *((int *)(idx + 4));
                            *((unsigned int *)(idx + v94 + 280)) = v110;
                            v101 = MulV(*((int *)iter), v53);
                            *((int *)(idx + v94 + 128)) = *((int *)(iter + 4));
                            v49 = v48 & 0xffffffff;
LABEL_14362deb2:
                            *((unsigned int *)(idx + v94 + 0x200)) = v101;
                            *((unsigned int *)(idx + v94 + 384)) = v101;
LABEL_14362dec4:
                            k = v91;
                            if (*((short *)v92) < 14)
                            {
                                v111 = *((short *)v92);
                                iter1 += (&g_14446b9d0)[v111];
                                iter += (&g_14446b9e0)[v111] * 8;
                                k = v91;
                            }
                        }
                        v93 += 4;
                        v92 += 2;
                        v94 += 4;
                        v91 = k - 1;
                        *((unsigned long long *)(idx + 736)) = v91;
                    } while (k != 1);
                    v90 = *((int *)(idx + 392));
                    v89 = *((int *)(idx + 388));
                    v88 = *((int *)(idx + 384));
                    v87 = *((int *)(idx + 520));
                    v86 = *((int *)(idx + 516));
                    v85 = *((int *)(idx + 0x200));
                    v83 = (int)*((int *)(idx + 0x88));
                    v82 = (int)*((int *)(idx + 132));
                    v81 = (int)*((int *)(idx + 128));
                    j = *((long long *)(idx + 808));
                    node = *((long long *)(idx + 704));
                    v64 = *((long long *)(idx + 864));
                }
                else if ((char)v65)
                {
                    *((unsigned int *)(rsp + 40)) = v31;
                    *((unsigned long long *)(rsp + 32)) = idx + 280;
                    v77 = idx + 640;
                    v78 = v41 & 0xffff;
                    v79 = v48 & 0xffffffff;
                    v80 = iter1;
                    if ((unsigned int)v48 < 3)
                    {
                        rsp = rsp - 8;
                        sub_14362b8b0(v80, v79, v78, v77, v103, a4);
                    }
                    else
                    {
                        rsp = rsp - 8;
                        sub_14362b750(v80, v79, v78, v77, v103, a4);
                    }
                    iter1 += 12;
                    v81 = (int)*((int *)(iter + 4));
                    v82 = (int)*((int *)(iter + 12));
                    v83 = (int)*((int *)(iter + 20));
                    v84 = iter + 24;
                    v85 = MulV(*((int *)iter), v53);
                    v86 = MulV(*((int *)(iter + 8)), v53);
                    v87 = MulV(*((int *)(iter + 16)), v53);
                    v88 = v85;
                    *((unsigned int *)(idx + 0x200)) = v85;
                    v89 = v86;
                    *((unsigned int *)(idx + 384)) = v85;
                    *((unsigned int *)(idx + 516)) = v86;
                    v90 = v87;
                    *((unsigned int *)(idx + 388)) = v86;
                    *((unsigned int *)(idx + 520)) = v87;
                    *((unsigned int *)(idx + 392)) = v87;
                    *((unsigned int *)(idx + 128)) = *((unsigned int *)&v81);
                    *((unsigned int *)(idx + 132)) = *((unsigned int *)&v82);
                    *((unsigned int *)(idx + 0x88)) = *((unsigned int *)&v83);
                    iter = v84;
                }
                else
                {
                    iter1 += 12;
                    iter += 24;
                    goto LABEL_14362dbfa;
                }
                if (!*((char *)(idx + 4)))
                {
LABEL_14362dbfa:
                    v59 = *((int128_t *)(idx + 0x100));
                    goto LABEL_14362dc01;
                }
                else
                {
                    if (j == 1)
                    {
                        *((unsigned int *)(idx + 384)) = MulV(v88, v55);
                        *((unsigned int *)(idx + 0x200)) = MulV(v85, v55);
                        *((unsigned int *)(idx + 128)) = *((unsigned int *)&MulV(v81, v55));
                        *((unsigned int *)(idx + 388)) = MulV(v89, v55);
                        *((unsigned int *)(idx + 516)) = MulV(v86, v55);
                        *((unsigned int *)(idx + 132)) = *((unsigned int *)&MulV(v82, v55));
                    }
                    else if (!j)
                    {
                        *((unsigned int *)(idx + 392)) = MulV(v90, v55);
                        *((unsigned int *)(idx + 520)) = MulV(v87, v55);
                        *((unsigned int *)(idx + 0x88)) = *((unsigned int *)&MulV(v83, v55));
                    }
                    v112 = *((int *)(idx + 640));
                    v113 = *((int *)(idx + 644));
                    v114 = *((int *)(idx + 648));
                    v115 = (int)*((int128_t *)(idx + 128));
                    v56 = (~(0xffffffff0000000000000000) & (~(0xffffffff00000000) & (CONCAT(CONCAT(v112, v112), CONCAT(v112, v112)) & 0xffffffff | ~(0xffffffff) & v56) | CONCAT(CONCAT(v113, v113), CONCAT(v113, v113)) & 0xffffffff00000000) | CONCAT(CONCAT(v114, v114), CONCAT(v114, v114)) & 0xffffffff0000000000000000) * *((int128_t *)(idx + 384)) + v115;
                    if (j != 1)
                    {
                        if (iter2 == 3)
                        {
                            v164 = v56;
                        }
                        else
                        {
                            v165 = *((int *)(idx + 280));
                            v166 = *((int *)(idx + 284));
                            v167 = *((int *)(idx + 288));
                            v168 = *((int128_t *)(idx + 960));
                            v169 = (~(0xffffffff0000000000000000) & (~(0xffffffff00000000) & (CONCAT(CONCAT(v165, v165), CONCAT(v165, v165)) & 0xffffffff | ~(0xffffffff) & v51) | CONCAT(CONCAT(v166, v166), CONCAT(v166, v166)) & 0xffffffff00000000) | CONCAT(CONCAT(v167, v167), CONCAT(v167, v167)) & 0xffffffff0000000000000000) * *((int128_t *)(idx + 0x200)) + v115;
                            *((uint128_t *)(idx + 976)) = (uint128_t)v169;
                            v164 = CONCAT(CONCAT(v168, v168), CONCAT(v168, v168)) * (v169 - v56) + v56;
                        }
                        v170 = *((char *)(*((long long *)(idx + 696)) + v64));
                        if (!j)
                        {
                            *((uint128_t *)(idx + 0x100)) = (uint128_t)v164;
                            v59 = (uint128_t)v164;
                            if (v170 & 16)
                            {
                                v59 /= v61;
                                *((uint128_t *)(idx + 0x100)) = v59;
                            }
LABEL_14362dc01:
                            v40 = *((char *)idx);
LABEL_14362dc06:
                            goto LABEL_14362dc0a;
                        }
                        else
                        {
                            v59 = *((int128_t *)(idx + 0x100));
                            v40 = *((char *)idx);
                            *((uint128_t *)(idx + 0x300)) = (uint128_t)v164;
                            if (v170 & 16)
                                *((uint128_t *)(idx + 0x300)) = (uint128_t)(v164 / v61);
LABEL_14362dc11:
                            v51 = (int)*((int128_t *)(idx + 976));
                            node += 6;
                            v50 = *((int128_t *)(idx + 992));
                            v48 = *((int *)(idx + 276));
                            v49 = *((long long *)(idx + 800));
                            *((unsigned long *)(idx + 704)) = node;
                        }
                    }
                    else if (iter2 == 3)
                    {
                        *((uint128_t *)(idx + 816)) = (uint128_t)(v56 * g_145f84100);
                        rsp = rsp - 8;
                        sub_14362f220(idx + 816, idx + 0x400, idx + 1008);
                        v116 = (int)*((int128_t *)(idx + 0x400));
                        v117 = (int)*((int128_t *)(idx + 1008));
                        v118 = (unsigned int)(v116 >> 64);
                        v119 = CONCAT(CONCAT((unsigned int)(v117 >> 64), (unsigned int)(v117 >> 64)), CONCAT((unsigned int)(v117 >> 64), (unsigned int)(v117 >> 64)));
                        v120 = CONCAT(CONCAT((unsigned int)((unsigned long long)v117 >> 32), (unsigned int)((unsigned long long)v117 >> 32)), CONCAT((unsigned int)((unsigned long long)v117 >> 32), (unsigned int)((unsigned long long)v117 >> 32)));
                        v121 = (unsigned long long)v116 >> 32;
                        v122 = v121 * v118;
                        v123 = v120 * v119;
                        v124 = v121 * (unsigned int)v119;
                        v125 = (int)(CONCAT(CONCAT((unsigned int)v120 * v118, (unsigned int)v120 * v118), CONCAT((unsigned int)v120 * v118, (unsigned int)v120 * v118)));
                        v52 = ~(0xffffffff000000000000000000000000) & (~(0xffffffff0000000000000000) & (~(0xffffffff00000000) & ((0x80000000800000008000000080000000 ^ v122) & 0xffffffff | ~(0xffffffff) & v52) | CONCAT(CONCAT(v124, v124), CONCAT(v124, v124)) & 0xffffffff00000000) | v125 & 0xffffffff0000000000000000) | CONCAT(CONCAT((unsigned int)v123, (unsigned int)v123), CONCAT((unsigned int)v123, (unsigned int)v123)) & 0xffffffff000000000000000000000000;
                        v126 = ~(0xffffffff) & *((int128_t *)(idx + 880)) | 0xffffffff & v123;
                        *((uint128_t *)(idx + 816)) = (uint128_t)v52;
                        v127 = (uint128_t)(~(0xffffffff000000000000000000000000) & (~(0xffffffff0000000000000000) & (~(0xffffffff00000000) & v126 | v125 & 0xffffffff00000000) | CONCAT(CONCAT(0x80000000 ^ v124, 0x80000000 ^ v124), CONCAT(0x80000000 ^ v124, 0x80000000 ^ v124)) & 0xffffffff0000000000000000) | CONCAT(CONCAT(v122, v122), CONCAT(v122, v122)) & 0xffffffff000000000000000000000000);
                        *((uint128_t *)(idx + 880)) = v127;
                        *((uint128_t *)(idx + 752)) = (uint128_t)(CONCAT(CONCAT((unsigned int)v116, (unsigned int)v116), CONCAT((unsigned int)v116, (unsigned int)v116)) * v127 + CONCAT(CONCAT((unsigned int)v117, (unsigned int)v117), CONCAT((unsigned int)v117, (unsigned int)v117)) * v52);
                        goto LABEL_14362dbfa;
                    }
                    else
                    {
                        v128 = *((int *)(idx + 284));
                        v129 = *((int *)(idx + 288));
                        v130 = *((int *)(idx + 280));
                        v131 = (~(0xffffffff0000000000000000) & (~(0xffffffff00000000) & (CONCAT(CONCAT(v130, v130), CONCAT(v130, v130)) & 0xffffffff | ~(0xffffffff) & *((int128_t *)(idx + 896))) | CONCAT(CONCAT(v128, v128), CONCAT(v128, v128)) & 0xffffffff00000000) | CONCAT(CONCAT(v129, v129), CONCAT(v129, v129)) & 0xffffffff0000000000000000) * *((int128_t *)(idx + 0x200));
                        *((uint128_t *)(idx + 128)) = (uint128_t)(v56 * g_145f84100);
                        v132 = v131 + v115;
                        *((uint128_t *)(idx + 896)) = (uint128_t)v132;
                        sub_14362f220(idx + 128, idx + 1056, idx + 1040);
                        v133 = (int)*((int128_t *)(idx + 1056));
                        v134 = (int)*((int128_t *)(idx + 1040));
                        v135 = (unsigned int)(v133 >> 64);
                        v136 = CONCAT(CONCAT((unsigned int)(v134 >> 64), (unsigned int)(v134 >> 64)), CONCAT((unsigned int)(v134 >> 64), (unsigned int)(v134 >> 64)));
                        v137 = CONCAT(CONCAT((unsigned int)((unsigned long long)v134 >> 32), (unsigned int)((unsigned long long)v134 >> 32)), CONCAT((unsigned int)((unsigned long long)v134 >> 32), (unsigned int)((unsigned long long)v134 >> 32)));
                        v138 = (unsigned long long)v133 >> 32;
                        v139 = v138 * v135;
                        v140 = v138 * (unsigned int)v136;
                        v141 = v137 * v136;
                        v142 = (int)(CONCAT(CONCAT((unsigned int)v137 * v135, (unsigned int)v137 * v135), CONCAT((unsigned int)v137 * v135, (unsigned int)v137 * v135)));
                        v143 = (uint128_t)(~(0xffffffff000000000000000000000000) & (~(0xffffffff0000000000000000) & (~(0xffffffff00000000) & ((0x80000000800000008000000080000000 ^ v139) & 0xffffffff | ~(0xffffffff) & *((int128_t *)(idx + 912))) | CONCAT(CONCAT(v140, v140), CONCAT(v140, v140)) & 0xffffffff00000000) | 0xffffffff0000000000000000 & v142) | CONCAT(CONCAT((unsigned int)v141, (unsigned int)v141), CONCAT((unsigned int)v141, (unsigned int)v141)) & 0xffffffff000000000000000000000000);
                        *((uint128_t *)(idx + 912)) = v143;
                        v144 = v132 * g_145f84100;
                        v145 = (uint128_t)(~(0xffffffff000000000000000000000000) & (~(0xffffffff0000000000000000) & (~(0xffffffff00000000) & (~(0xffffffff) & *((int128_t *)(idx + 928)) | 0xffffffff & v141) | 0xffffffff00000000 & v142) | CONCAT(CONCAT(0x80000000 ^ v140, 0x80000000 ^ v140), CONCAT(0x80000000 ^ v140, 0x80000000 ^ v140)) & 0xffffffff0000000000000000) | CONCAT(CONCAT(v139, v139), CONCAT(v139, v139)) & 0xffffffff000000000000000000000000);
                        *((uint128_t *)(idx + 928)) = v145;
                        *((uint128_t *)(idx + 128)) = (uint128_t)v144;
                        v146 = CONCAT(CONCAT((unsigned int)v134, (unsigned int)v134), CONCAT((unsigned int)v134, (unsigned int)v134)) * v143 + CONCAT(CONCAT((unsigned int)v133, (unsigned int)v133), CONCAT((unsigned int)v133, (unsigned int)v133)) * v145;
                        rsp = rsp - 16;
                        sub_14362f220(idx + 128, idx + 1088, idx + 1072);
                        v147 = (int)*((int128_t *)(idx + 1088));
                        v148 = (int)*((int128_t *)(idx + 1072));
                        v149 = (unsigned int)(v147 >> 64);
                        v150 = (unsigned int)(v148 >> 64);
                        v151 = (unsigned long long)v148 >> 32;
                        v152 = (unsigned long long)v147 >> 32;
                        v153 = v151 * v150;
                        v154 = v152 * v149;
                        v155 = v152 * v150;
                        v156 = (int)(CONCAT(CONCAT(v151 * v149, v151 * v149), CONCAT(v151 * v149, v151 * v149)));
                        v157 = v153 | ~(0xffffffff) & *((int128_t *)(idx + 944));
                        *((uint128_t *)(idx + 832)) = (uint128_t)(~(0xffffffff000000000000000000000000) & (~(0xffffffff0000000000000000) & (~(0xffffffff00000000) & ((0x80000000800000008000000080000000 ^ v154) & 0xffffffff | ~(0xffffffff) & *((int128_t *)(idx + 832))) | CONCAT(CONCAT(v155, v155), CONCAT(v155, v155)) & 0xffffffff00000000) | v156 & 0xffffffff0000000000000000) | CONCAT(CONCAT(v153, v153), CONCAT(v153, v153)) & 0xffffffff000000000000000000000000);
                        v158 = *((int128_t *)(idx + 960));
                        v40 = *((char *)idx);
                        v59 = *((int128_t *)(idx + 0x100));
                        v159 = (int)(CONCAT(CONCAT((unsigned int)v148, (unsigned int)v148), CONCAT((unsigned int)v148, (unsigned int)v148)) * *((int128_t *)(idx + 832)));
                        v160 = (uint128_t)(~(0xffffffff000000000000000000000000) & (~(0xffffffff0000000000000000) & (~(0xffffffff00000000) & v157 | v156 & 0xffffffff00000000) | CONCAT(CONCAT(0x80000000 ^ v155, 0x80000000 ^ v155), CONCAT(0x80000000 ^ v155, 0x80000000 ^ v155)) & 0xffffffff0000000000000000) | CONCAT(CONCAT(v154, v154), CONCAT(v154, v154)) & 0xffffffff000000000000000000000000);
                        *((uint128_t *)(idx + 944)) = v160;
                        v161 = (uint128_t)(v159 + CONCAT(CONCAT((unsigned int)v147, (unsigned int)v147), CONCAT((unsigned int)v147, (unsigned int)v147)) * v160);
                        v162 = (unsigned int)((unsigned long long)v146 * (unsigned long long)v161 >> 32) + (unsigned int)v146 * (unsigned int)v161 + (unsigned int)(v146 * v161 >> 64) + (unsigned int)(v146 * v161 >> 96);
                        v52 = (int)*((int128_t *)(idx + 816));
                        *((uint128_t *)(idx + 752)) = (CONCAT(CONCAT(v158, v158), CONCAT(v158, v158)) * (((0x80000000800000008000000080000000 ^ v161) & CmpLTV(CONCAT(CONCAT(v162, v162), CONCAT(v162, v162)), 0) | ~(CmpLTV(CONCAT(CONCAT(v162, v162), CONCAT(v162, v162)), 0)) & v161) - v146) + v146) * 0x3f8000003f8000003f8000003f800000 / unsupported_Iop_Sqrt32Fx4();
LABEL_14362dc0a:
                        v31 = (unsigned int)v12;
                        v55 = v17;
                        v53 = v18;
                        goto LABEL_14362dc11;
                    }
                }
                v61 = *((int128_t *)(idx + 848));
                j += 1;
                v65 = *((int *)(idx + 4));
                *((long long *)(idx + 808)) = j;
            } while (j < 3);
            v60 = *((int128_t *)(idx + 0x300));
            v28 = (int)*((int128_t *)(idx + 672));
            v47 = *((char *)(idx + 1));
            v171 = v47;
            v172 = *((long long *)(rsp + 0x1600));
            if (v172)
            {
                v173 = v171 & 0xff;
                idx2 = v173 * 6;
                *((int128_t *)(v172 + idx2 * 8 + 16)) = *((int128_t *)(idx + 752));
                *((uint128_t *)(v172 + idx2 * 8 + 32)) = v59;
                *((uint128_t *)(v172 + idx2 * 8)) = v60;
            }
            else
            {
                index = *((long long *)(rsp + 5640));
                v176 = (int)*((int128_t *)(idx + 752));
                *((uint128_t *)(idx + 384)) = v59;
                *((uint128_t *)(idx + 0x100)) = (uint128_t)v176;
                v177 = &index->field_e0->field_0;
                *((uint128_t *)(idx + 128)) = v60;
                if (v177 && !(char)v171)
                {
                    *((unsigned long long *)(rsp + 32)) = index->field_e8;
                    v177();
                }
                v178 = index->field_7d;
                v179 = index->field_80;
                v180 = (int)(CONCAT(CONCAT((unsigned int)v28, (unsigned int)v28), CONCAT((unsigned int)v28, (unsigned int)v28)));
                v181 = (uint128_t)(v59 * v180);
                v173 = v171 & 0xff;
                v182 = v176 * v180;
                v183 = (uint128_t)(v60 * v180);
                *((uint128_t *)(idx + 384)) = v181;
                *((uint128_t *)(idx + 0x100)) = (uint128_t)v182;
                *((uint128_t *)(idx + 128)) = v183;
                if ((char)v178 > 0)
                {
                    v184 = v173 * 6;
                    v181 += *((int128_t *)(v179 + v184 * 8 + 32));
                    *((uint128_t *)(idx + 384)) = v181;
                    v185 = v182 * *((int128_t *)(v179 + v184 * 8 + 16));
                    v186 = (unsigned int)((unsigned long long)v185 >> 32) + (unsigned int)v185;
                    v187 = (int)(CmpLTV(CONCAT(CONCAT(v186 + (unsigned int)(v185 >> 64) + (unsigned int)(v185 >> 96), v186 + (unsigned int)(v185 >> 64) + (unsigned int)(v185 >> 96)), CONCAT(v186 + (unsigned int)(v185 >> 64) + (unsigned int)(v185 >> 96), v186 + (unsigned int)(v185 >> 64) + (unsigned int)(v185 >> 96))), 0));
                    v188 = (uint128_t)((0x80000000800000008000000080000000 ^ v182) & v187 | ~(v187) & v182);
                    *((uint128_t *)(idx + 0x100)) = v188;
                    *((uint128_t *)(idx + 0x100)) = v188 + *((int128_t *)(v179 + v184 * 8 + 16));
                    *((uint128_t *)(idx + 128)) = v183 + *((int128_t *)(v179 + v184 * 8));
                }
                v189 = v173 * 6;
                *((uint128_t *)(v179 + v189 * 8 + 32)) = v181;
                *((int128_t *)(v179 + v189 * 8 + 16)) = *((int128_t *)(idx + 0x100));
                *((int128_t *)(v179 + v189 * 8)) = *((int128_t *)(idx + 128));
                *((char *)(v173 + index->field_b0)) = 0;
            }
            v48 = *((int *)(idx + 276));
            v50 = *((int128_t *)(idx + 992));
            v47 = _INSERT(v171, 0, (char)v171 + 1);
            v46 = v47 & 0xff;
            v49 = v48 & 0xffffffff;
            *((char *)(idx + 1)) = (char)v171 + 1;
            *((uint128_t *)(idx + v173 * 16 + 1104)) = v61 * v60;
        } while ((unsigned int)v46 < *((int *)(idx + 272)));
    }
    if (!*((long long *)(rsp + 0x1600)))
        v46 = sub_14362ea90(*((long long *)(rsp + 5608)), *((long long *)(rsp + 5640)) + 200);
    return v46;
}

