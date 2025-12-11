#!/usr/bin/env python3
"""
手动CSV修复脚本
Manual CSV Fix Script

基于已知的课文结构手动修复CSV数据
"""

import pandas as pd
from pathlib import Path


def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾", "🚀": "🚀"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def create_manual_lesson_data():
    """
    创建手动的课文数据结构
    基于之前分析的PDF内容
    """
    lessons = []

    # 第一单元 (页2-12)
    first_unit_lessons = [
        {"unit_number": 1, "lesson_number": 1, "lesson_title": "大青树下的小学", "start_page": 7, "end_page": 10},
        {"unit_number": 1, "lesson_number": 2, "lesson_title": "花的学校", "start_page": 10, "end_page": 12},
        {"unit_number": 1, "lesson_number": 3, "lesson_title": "不懂就要问", "start_page": 12, "end_page": 13},
    ]

    # 第二单元 (页13-26)
    second_unit_lessons = [
        {"unit_number": 2, "lesson_number": 4, "lesson_title": "古诗三首", "start_page": 14, "end_page": 15},
        {"unit_number": 2, "lesson_number": 5, "lesson_title": "山行", "start_page": 14, "end_page": 14},
        {"unit_number": 2, "lesson_number": 6, "lesson_title": "赠刘景文", "start_page": 14, "end_page": 14},
        {"unit_number": 2, "lesson_number": 7, "lesson_title": "夜书所见", "start_page": 15, "end_page": 15},
        {"unit_number": 2, "lesson_number": 8, "lesson_title": "铺满金色巴掌的水泥道", "start_page": 16, "end_page": 18},
        {"unit_number": 2, "lesson_number": 9, "lesson_title": "秋天的雨", "start_page": 19, "end_page": 22},
        {"unit_number": 2, "lesson_number": 10, "lesson_title": "听听，秋的声音", "start_page": 22, "end_page": 25},
    ]

    # 第三单元 (页27-44)
    third_unit_lessons = [
        {"unit_number": 3, "lesson_number": 11, "lesson_title": "卖火柴的小女孩", "start_page": 28, "end_page": 32},
        {"unit_number": 3, "lesson_number": 12, "lesson_title": "那一定会很好", "start_page": 33, "end_page": 34},
        {"unit_number": 3, "lesson_number": 13, "lesson_title": "在牛肚子里旅行", "start_page": 35, "end_page": 37},
        {"unit_number": 3, "lesson_number": 14, "lesson_title": "一块奶酪", "start_page": 38, "end_page": 42},
    ]

    # 第四单元 (页45-62)
    fourth_unit_lessons = [
        {"unit_number": 4, "lesson_number": 15, "lesson_title": "总也倒不了的老屋", "start_page": 46, "end_page": 49},
        {"unit_number": 4, "lesson_number": 16, "lesson_title": "胡萝卜先生的长胡子", "start_page": 50, "end_page": 52},
        {"unit_number": 4, "lesson_number": 17, "lesson_title": "小狗学叫", "start_page": 53, "end_page": 58},
    ]

    # 第五单元 (页63-72)
    fifth_unit_lessons = [
        {"unit_number": 5, "lesson_number": 18, "lesson_title": "搭船的鸟", "start_page": 64, "end_page": 65},
        {"unit_number": 5, "lesson_number": 19, "lesson_title": "金色的草地", "start_page": 66, "end_page": 71},
    ]

    # 第六单元 (页73-86)
    sixth_unit_lessons = [
        {"unit_number": 6, "lesson_number": 20, "lesson_title": "古诗三首", "start_page": 74, "end_page": 75},
        {"unit_number": 6, "lesson_number": 21, "lesson_title": "望天门山", "start_page": 74, "end_page": 74},
        {"unit_number": 6, "lesson_number": 22, "lesson_title": "饮湖上初晴后雨", "start_page": 74, "end_page": 74},
        {"unit_number": 6, "lesson_number": 23, "lesson_title": "望洞庭", "start_page": 75, "end_page": 75},
        {"unit_number": 6, "lesson_number": 24, "lesson_title": "富饶的西沙群岛", "start_page": 76, "end_page": 78},
        {"unit_number": 6, "lesson_number": 25, "lesson_title": "海滨小城", "start_page": 79, "end_page": 80},
        {"unit_number": 6, "lesson_number": 26, "lesson_title": "美丽的小兴安岭", "start_page": 81, "end_page": 86},
    ]

    # 第七单元 (页87-100)
    seventh_unit_lessons = [
        {"unit_number": 7, "lesson_number": 27, "lesson_title": "大自然的声音", "start_page": 88, "end_page": 92},
        {"unit_number": 7, "lesson_number": 28, "lesson_title": "读不完的大书", "start_page": 91, "end_page": 93},
        {"unit_number": 7, "lesson_number": 29, "lesson_title": "父亲、树林和鸟", "start_page": 94, "end_page": 99},
    ]

    # 第八单元 (页101-113)
    eighth_unit_lessons = [
        {"unit_number": 8, "lesson_number": 30, "lesson_title": "司马光", "start_page": 102, "end_page": 103},
        {"unit_number": 8, "lesson_number": 31, "lesson_title": "掌声", "start_page": 103, "end_page": 104},
        {"unit_number": 8, "lesson_number": 32, "lesson_title": "手术台就是阵地", "start_page": 105, "end_page": 110},
    ]

    # 合并所有课文
    lessons.extend(first_unit_lessons)
    lessons.extend(second_unit_lessons)
    lessons.extend(third_unit_lessons)
    lessons.extend(fourth_unit_lessons)
    lessons.extend(fifth_unit_lessons)
    lessons.extend(sixth_unit_lessons)
    lessons.extend(seventh_unit_lessons)
    lessons.extend(eighth_unit_lessons)

    # 添加单元标题
    for lesson in lessons:
        lesson['unit_title'] = f"第{lesson['unit_number']}单元"

    return lessons


def fix_csv_manually(csv_path: str, output_path: str):
    """
    手动修复CSV文件结构

    Args:
        csv_path: 输入CSV文件路径
        output_path: 输出CSV文件路径
    """
    print_status(f"读取CSV文件: {csv_path}", "📚")

    # 读取原始CSV
    df = pd.read_csv(csv_path)

    print(f"📊 原始数据:")
    print(f"  总行数: {len(df)}")

    # 获取正确的课文数据
    correct_lessons = create_manual_lesson_data()

    print(f"📋 手动创建了 {len(correct_lessons)} 篇课文")

    # 修复每一行
    print_status("开始修复数据行", "🔧")

    fixed_rows = []
    for idx, row in df.iterrows():
        page_num = row['page_number']

        # 查找最匹配的课文
        best_lesson = None
        min_distance = float('inf')

        for lesson in correct_lessons:
            # 计算页面距离
            distance = abs(page_num - lesson['start_page'])
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
            fixed_row['lesson_start_page'] = best_lesson['start_page']
            fixed_row['lesson_end_page'] = best_lesson['end_page']
        else:
            # 清除课文信息（可能是目录、封面等）
            if page_num <= 6:  # 前6页通常是封面、目录等
                fixed_row['unit_number'] = None
                fixed_row['unit_title'] = None
                fixed_row['lesson_number'] = None
                fixed_row['lesson_title'] = None
                fixed_row['lesson_start_page'] = None
                fixed_row['lesson_end_page'] = None
            else:
                # 保留原文但清除错误的课文信息
                fixed_row['unit_number'] = None
                fixed_row['unit_title'] = None
                fixed_row['lesson_number'] = None
                fixed_row['lesson_title'] = None
                fixed_row['lesson_start_page'] = None
                fixed_row['lesson_end_page'] = None

        fixed_rows.append(fixed_row)

    # 创建新的DataFrame
    fixed_df = pd.DataFrame(fixed_rows)

    # 保存修复后的CSV
    fixed_df.to_csv(output_path, index=False, encoding='utf-8-sig')

    print_status(f"修复后的数据已保存: {output_path}", "✅")

    # 显示统计信息
    print(f"📊 修复后统计:")
    print(f"  总行数: {len(fixed_df)}")
    print(f"  有课文信息: {fixed_df['lesson_title'].notna().sum()}")

    # 按单元统计
    if fixed_df['lesson_title'].notna().any():
        unit_stats = fixed_df[fixed_df['lesson_title'].notna()].groupby('unit_number').agg({
            'lesson_title': 'nunique',
            'content_length': 'mean'
        }).round(1)

        print(f"  按单元统计:")
        for unit_num, row in unit_stats.iterrows():
            if pd.notna(unit_num):
                print(f"    第{int(unit_num)}单元: {int(row['lesson_title'])}篇课文, 平均长度{row['content_length']:.1f}字符")

    return fixed_df


def main():
    """主函数"""
    print("🔧 手动CSV修复工具")
    print("=" * 30)
    print()

    # 输入输出文件路径
    input_csv = "exports/语文三上_content.csv"
    output_csv = "exports/语文三上_content_fixed.csv"

    if not Path(input_csv).exists():
        print_status(f"输入文件不存在: {input_csv}", "❌")
        return 1

    try:
        fixed_df = fix_csv_manually(input_csv, output_csv)

        print()
        print("🎉 手动CSV修复完成!")
        print(f"📁 输出文件: {output_csv}")
        print()
        print("📋 课文结构预览:")

        # 显示课文预览
        lessons = create_manual_lesson_data()
        for lesson in lessons[:10]:  # 显示前10篇
            print(f"  第{lesson['unit_number']}单元 第{lesson['lesson_number']}课: {lesson['lesson_title']} (页{lesson['start_page']}-{lesson['end_page']})")

        if len(lessons) > 10:
            print(f"  ... 还有 {len(lessons) - 10} 篇课文")

        return 0

    except Exception as e:
        print_status(f"修复失败: {e}", "❌")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())