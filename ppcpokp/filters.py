# app/filters.py
import re

def remove_parentheses(text):
    """删除圆括号及括号中的内容"""
    if not text:
        return text
    return re.sub(r'\([^)]*\)', '', text)

def remove_all_brackets(text):
    """使用栈处理嵌套括号及其内容"""
    if not text:
        return text
    
    # 定义括号映射
    bracket_map = {')': '(', ']': '[', '}': '{'}
    opening_brackets = set(bracket_map.values())
    closing_brackets = set(bracket_map.keys())
    
    # 栈，存储(位置, 括号类型)
    stack = []
    # 记录需要删除的范围
    to_remove = []
    
    for i, char in enumerate(text):
        if char in opening_brackets:
            # 左括号入栈
            stack.append((i, char))
        elif char in closing_brackets:
            if stack:
                # 获取栈顶元素
                top_idx, top_char = stack[-1]
                # 检查是否匹配
                if bracket_map[char] == top_char:
                    # 匹配成功，记录需要删除的范围
                    to_remove.append((top_idx, i))
                    stack.pop()
                else:
                    # 括号不匹配，清空栈（处理错误嵌套）
                    stack = []
            else:
                # 没有匹配的左括号，忽略这个右括号
                pass
    
    # 按照起始位置从后往前删除，避免索引变化
    to_remove.sort(reverse=True)
    result = list(text)
    
    for start, end in to_remove:
        # 将删除范围内的字符替换为空
        for i in range(start, end + 1):
            result[i] = ''
    
    return ''.join(result)

def strip_brackets(text, keep_content=False):
    """
    删除括号，可选择是否保留内容
    keep_content: True - 删除括号保留内容，False - 删除括号及内容
    """
    if not text:
        return text
    
    if keep_content:
        # 只删除括号，保留内容
        return re.sub(r'[\(\)\[\]\{\}]', '', text)
    else:
        # 删除括号及内容
        return re.sub(r'\([^)]*\)|\[[^\]]*\]|\{[^}]*\}', '', text)

def capitalize_first(s):
    """将字符串的第一个字母大写"""
    if not s:
        return s
    return s[0].upper() + s[1:]
