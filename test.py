from function_process import *



# 示例用法
function_string = """void switch_case_example(int value) {
    switch (value) {
        case 1:
        {
            printf("You selected One\n");
            break;
        }
        case 2:
        {
            printf("You selected Two\n");
            break;
        }
        case 3:
        {
            printf("You selected Three\n");
            break;
        }
        default:
        {
            printf("Unknown selection\n");
            break;
        }
    }
}"""

_, b, _ = extract_switch_case_block(function_string)

print(b)