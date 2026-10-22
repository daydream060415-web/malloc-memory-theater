#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    size_t count = 3;
    int *scores = NULL;
    /* 在乘法之前检查，避免分配字节数发生无符号溢出。 */
    if (count > SIZE_MAX / sizeof *scores) return EXIT_FAILURE;
    scores = malloc(count * sizeof *scores);
    if (scores == NULL) {
        fputs("Allocation failed\n", stderr);
        return EXIT_FAILURE;
    }
    /* malloc 不初始化数据：先写入，再读取。 */
    for (size_t i = 0; i < count; ++i) scores[i] = 80 + (int)i * 5;
    size_t new_count = 5;
    if (new_count > SIZE_MAX / sizeof *scores) {
        free(scores);
        return EXIT_FAILURE;
    }
    /* 用临时指针接收结果，避免失败时丢失原分配。 */
    int *next = realloc(scores, new_count * sizeof *scores);
    if (next == NULL) {
        free(scores);
        fputs("Resize failed\n", stderr);
        return EXIT_FAILURE;
    }
    scores = next;
    for (size_t i = count; i < new_count; ++i) scores[i] = 95;
    count = new_count;
    int sum = 0;
    for (size_t i = 0; i < count; ++i) sum += scores[i];
    printf("count=%zu, sum=%d, average=%.1f\n", count, sum, (double)sum / count);
    free(scores);
    scores = NULL;
    return EXIT_SUCCESS;
}
