ERROR    | 2026-09-17 06:48:05,489 | angr.state_plugins.unicorn_engine | failed loading "unicornlib.dylib", unicorn support disabled ('NoneType' object has no attribute 'unicorn_py3')
// ---- 0x1430385c0
typedef struct st_1430385c0_0 {
    char padding_0[264];
    struct st_1430385c0_1 *field_108;
} st_1430385c0_0;

typedef struct st_1430385c0_2 {
    char padding_0[8];
    struct st_1430385c0_3 *field_8;
    char padding_10[8];
    long long field_18;
    char padding_20[24];
    long long field_38;
} st_1430385c0_2;

typedef struct st_1430385c0_3 {
    struct st_1430385c0_0 *field_0;
} st_1430385c0_3;

typedef struct st_1430385c0_1 {
    unsigned long long field_0;
} st_1430385c0_1;

char sub_1430385c0(st_1430385c0_2 *a0, char a1)
{
    char v0;  // [bp-0x58]
    unsigned long long v1;  // [bp-0x40]
    unsigned int v2;  // [bp+0x8]
    unsigned int v3;  // [bp+0x18]
    unsigned int v4;  // [bp+0x20]

    if (!a0->field_8)
        return 0;
    sub_1400e31b0(a0->field_18);
    v1 = sub_1400e31b0(a0->field_38);
    v2 = 0xffffffff;
    v3 = 0xffffffff;
    v4 = 0;
    v0 = a1;
    a0->field_8->field_0->field_108();
}

