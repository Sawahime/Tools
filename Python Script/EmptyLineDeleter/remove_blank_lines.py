import sys

def remove_blank_lines(input_file, output_file=None):
    """
    删除文件中的空白行
    :param input_file: 输入文件路径
    :param output_file: 输出文件路径(可选，默认为覆盖原文件)
    """
    # 读取文件内容并过滤空白行
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line for line in f if line.strip() != '']
    
    # 确定输出文件路径
    output_path = output_file if output_file else input_file
    
    # 写入处理后的内容
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"已成功处理文件: {input_file} -> {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python remove_blank_lines.py <输入文件> [输出文件]")
        print("示例:")
        print("  python remove_blank_lines.py input.txt")  # 覆盖原文件
        print("  python remove_blank_lines.py input.txt output.txt")  # 输出到新文件
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        remove_blank_lines(input_file, output_file)
    except Exception as e:
        print(f"处理文件时出错: {e}")
        sys.exit(1)