#!/usr/bin/env python3
"""
CSV数据结构修复脚本
Fix CSV Data Structure Script

修复从PDF导出的CSV文件中的课文结构信息
"""

import pandas as pd
import re
from typing import List, Dict, Any
from pathlib import Path


def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾", "🚀": "🚀"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def extract_lessons_from_directory_content(directory_text: str) -> List[Dict[str, Any]]:
    """
    从目录内容中提取正确的课文信息

    Args:
        directory_text: 目录页的文本内容

    Returns:
        课文信息列表
    """
    lessons = []

    # 按单元分割
    unit_sections = re.split(r'第([一二三四五六七八九十\d]+)单元', directory_text)

    for i in range(1, len(unit_sections), 2):
        if i >= len(unit_sections) - 1:
            break

        unit_chinese = unit_sections[i]
        unit_content = unit_sections[i + 1]

        unit_number = chinese_to_int(unit_chinese)

        # 在单元内容中查找课文
        # 格式：1 大青树下的小学...................2
        lesson_pattern = r'(\d+)\s+([^。\n]{2,30})(?:\*{0,2})(?:\.{4,})?\s*(\d+)'
        lesson_matches = re.findall(lesson_pattern, unit_content)

        for lesson_num_str, lesson_title, page_num in lesson_matches:
            lesson_title = lesson_title.strip()

            # 过滤掉非课文内容
            if (len(lesson_title) > 1 and
                not any(skip in lesson_title for skip in [
                    '口语交际', '习作', '语文园地', '快乐读书吧',
                    '识字表', '写字表', '词语表', '标*的是'
                ])):

                lessons.append({
                    'unit_number': unit_number,
                    'unit_title': f"第{unit_number}单元",
                    'lesson_number': int(lesson_num_str),
                    'lesson_title': lesson_title,
                    'lesson_start_page': int(page_num)
                })

    return lessons


def chinese_to_int(chinese_str: str) -> int:
    """将中文数字转换为整数"""
    chinese_map = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
    }

    if chinese_str.isdigit():
        return int(chinese_str)

    if chinese_str in chinese_map:
        return chinese_map[chinese_str]

    return int(chinese_str)  # 默认转换


def fix_csv_structure(csv_path: str, output_path: str):
    """
    修复CSV文件的结构

    Args:
        csv_path: 输入CSV文件路径
        output_path: 输出CSV文件路径
    """
    print_status(f"读取CSV文件: {csv_path}", "📚")

    # 读取CSV文件
    df = pd.read_csv(csv_path)

    print(f"📊 原始数据:")
    print(f"  总行数: {len(df)}")
    print(f"  有课文信息: {df['lesson_title'].notna().sum()}")

    # 查找目录页内容（通常包含所有课文标题）
    directory_content = ""
    for idx, row in df.iterrows():
        if '目录' in row['content'] or '第一单元' in row['content']:
            directory_content = row['content']
            break

    if not directory_content:
        print_status("未找到目录内容，尝试从内容中提取", "⚠️")
        # 搜索包含多个课文的行
        for idx, row in df.iterrows():
            if re.search(r'1\s+\S+\s+2\s+\S+\s+3\s+\S+', row['content']):
                directory_content = row['content']
                break

    if not directory_content:
        print_status("无法找到目录内容", "❌")
        return

    print_status("从目录中提取课文信息", "🔍")

    # 提取正确的课文信息
    correct_lessons = extract_lessons_from_directory_content(directory_content)

    print(f"📋 提取到 {len(correct_lessons)} 篇课文:")
    for lesson in correct_lessons[:10]:  # 显示前10篇
        print(f"  第{lesson['unit_number']}单元 第{lesson['lesson_number']}课: {lesson['lesson_title']} (页{lesson['lesson_start_page']})")

    if len(correct_lessons) > 10:
        print(f"  ... 还有 {len(correct_lessons) - 10} 篇")

    # 创建课文映射字典
    lesson_map = {}
    for lesson in correct_lessons:
        key = (lesson['unit_number'], lesson['lesson_number'])
        lesson_map[key] = lesson

    # 修复每一行的课文信息
    print_status("开始修复数据行", "🔧")

    fixed_rows = []
    for idx, row in df.iterrows():
        page_num = row['page_number']

        # 查找最匹配的课文
        best_lesson = None
        min_distance = float('inf')

        for lesson in correct_lessons:
            # 计算页面距离
            distance = abs(page_num - lesson['lesson_start_page'])
            if distance < min_distance:
                min_distance = distance
                best_lesson = lesson

        # 更新行数据
        fixed_row = row.copy()
        if best_lesson and min_distance <= 5:  # 允许5页的误差
            fixed_row['unit_number'] = best_lesson['unit_number']
            fixed_row['unit_title'] = best_lesson['unit_title']
            fixed_row['lesson_number'] = best_lesson['lesson_number']
            fixed_row['lesson_title'] = best_lesson['lesson_title']
            fixed_row['lesson_start_page'] = best_lesson['lesson_start_page']
            fixed_row['lesson_end_page'] = None  # 稍后计算
        else:
            # 清除错误的课文信息
            if page_num < 50:  # 前50页可能是封面、目录等
                fixed_row['unit_number'] = None
                fixed_row['unit_title'] = None
                fixed_row['lesson_number'] = None
                fixed_row['lesson_title'] = None
                fixed_row['lesson_start_page'] = None
                fixed_row['lesson_end_page'] = None

        fixed_rows.append(fixed_row)

    # 计算每篇课文的结束页面
    print_status("计算课文结束页面", "📊")

    lesson_end_pages = {}
    for lesson in correct_lessons:
        # 找到同一篇课文的最后一页
        lesson_pages = [row['page_number'] for row in fixed_rows
                        if (row['unit_number'] == lesson['unit_number'] and
                            row['lesson_number'] == lesson['lesson_number'])]
        if lesson_pages:
            lesson_end_pages[(lesson['unit_number'], lesson['lesson_number'])] = max(lesson_pages)

    # 更新结束页面信息
    for row in fixed_rows:
        if row['unit_number'] and row['lesson_number']:
            key = (int(row['unit_number']), int(row['lesson_number']))
            if key in lesson_end_pages:
                row['lesson_end_page'] = lesson_end_pages[key]

    # 创建新的DataFrame
    fixed_df = pd.DataFrame(fixed_rows)

    # 保存修复后的CSV
    fixed_df.to_csv(output_path, index=False, encoding='utf-8-sig')

    print_status(f"修复后的数据已保存: {output_path}", "✅")

    # 显示统计信息
    print(f"📊 修复后统计:")
    print(f"  总行数: {len(fixed_df)}")
    print(f"  有课文信息: {fixed_df['lesson_title'].notna().sum()}")
    print(f"  单元数: {fixed_df['unit_number'].nunique()}")

    if fixed_df['unit_number'].notna().any():
        for unit_num in sorted(fixed_df['unit_number'].unique()):
            if pd.notna(unit_num):
                unit_lessons = fixed_df[
                    (fixed_df['unit_number'] == unit_num) &
                    (fixed_df['lesson_number'].notna())
                ]['lesson_title'].unique()
                print(f"  第{int(unit_num)}单元: {len(unit_lessons)}篇课文")

    return fixed_df


def main():
    """主函数"""
    print("🔧 CSV数据结构修复工具")
    print("=" * 40)
    print()

    # 输入输出文件路径
    input_csv = "exports/语文三上_content.csv"
    output_csv = "exports/语文三上_content_fixed.csv"

    if not Path(input_csv).exists():
        print_status(f"输入文件不存在: {input_csv}", "❌")
        return 1

    try:
        fixed_df = fix_csv_structure(input_csv, output_csv)

        print()
        print("🎉 CSV结构修复完成!")
        print(f"📁 输出文件: {output_csv}")
        print("📋 下一步:")
        print("  1. 检查修复后的CSV文件")
        print("  2. 验证课文信息的准确性")
        print("  3. 准备进行向量化处理")

        return 0

    except Exception as e:
        print_status(f"修复失败: {e}", "❌")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())