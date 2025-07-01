content = "12345678\n" * 1024 * 1024

with open("index.html", "w") as file:
    file.write(content)

print("内容已成功写入html文件")
