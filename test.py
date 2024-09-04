from utils import *

code_seq = \
"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 宏定义
#define MAX_NAME_LENGTH 50
#define PI 3.14159

// 枚举类型
enum Day {
    SUNDAY,
    MONDAY,
    TUESDAY,
    WEDNESDAY,
    THURSDAY,
    FRIDAY,
    SATURDAY
};

// 结构体定义
struct Person {
    char name[MAX_NAME_LENGTH];
    int age;
};

// 函数声明
void printGreeting();
int add(int a, int b);
double calculateCircleArea(double radius);
void printDay(enum Day day);
void readFile(const char *filename);

int main() {
    // 基本变量类型
    int a = 10;
    float b = 5.5;
    double c = 3.14159;
    char d = 'A';

    // 指针
    int *p = &a;
    printf("Value of a: %d\n", a);
    printf("Address of a: %p\n", (void*)&a);
    printf("Value of p (address of a): %p\n", (void*)p);
    printf("Dereferenced value of p: %d\n", *p);

    // 数组
    int arr[5] = {1, 2, 3, 4, 5};
    for (int i = 0; i < 5; i++) {
        printf("arr[%d] = %d\n", i, arr[i]);
    }

    // 结构体
    struct Person person;
    strcpy(person.name, "John Doe");
    person.age = 30;
    printf("Person: %s, Age: %d\n", person.name, person.age);

    // 函数调用
    printGreeting();
    int sum = add(3, 4);
    printf("Sum: %d\n", sum);

    if (1) {
        double area = calculateCircleArea(5.0);
        printf("Area of circle: %f\n", area);
    }
    
    printDay(MONDAY);

    // 文件操作
    const char *filename = "example.txt";
    readFile(filename);

    return 0;
}

// 函数定义
void printGreeting() {
    printf("Hello, world!\n");
}

int add(int a, int b) {
    return a + b;
}

double calculateCircleArea(double radius) {
    return PI * radius * radius;
}

void printDay(enum Day day) {
    switch(day) {
        case SUNDAY: printf("Sunday\n"); break;
        case MONDAY: printf("Monday\n"); break;
        case TUESDAY: printf("Tuesday\n"); break;
        case WEDNESDAY: printf("Wednesday\n"); break;
        case THURSDAY: printf("Thursday\n"); break;
        case FRIDAY: printf("Friday\n"); break;
        case SATURDAY: printf("Saturday\n"); break;
        default: printf("Invalid day\n"); break;
    }
}

void readFile(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (file == NULL) {
        perror("Error opening file");
        return;
    }
    
    char buffer[256];
    while (fgets(buffer, sizeof(buffer), file) != NULL) {
        printf("%s", buffer);
    }
    
    fclose(file);
}
"""

code_byte_seq = code_seq.encode('utf-8')

tree = parser.parse(code_byte_seq)
root_node = tree.root_node
query = C_LANGUAGE.query('(function_definition) @func_def')
captures = query.captures(root_node)

node = captures[4][0]
func = node.text.decode('utf-8')

pp = func.splitlines(True)
print(pp)
print(len(pp))