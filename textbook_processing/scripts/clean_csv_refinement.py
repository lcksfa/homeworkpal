#!/usr/bin/env python3
"""
CSV内容清理和精炼脚本
CSV Content Cleaning and Refinement Script

专门用于清理和精炼语文教材CSV文件，移除多余空白，区分课文与练习内容
"""

import os
import sys
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾", "📖": "📖", "🗑️": "🗑️"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def clean_whitespace(text: str) -> str:
    """清理文本中的多余空白"""
    if pd.isna(text) or not text:
        return text

    # 移除行首行尾空白
    text = str(text).strip()

    # 将多个连续空格替换为单个空格
    text = re.sub(r' +', ' ', text)

    # 将多个连续换行符替换为单个换行符
    text = re.sub(r'\n+', '\n', text)

    # 移除行首行尾的换行符
    text = text.strip()

    # 处理特殊的空白字符（如全角空格）
    text = re.sub(r'\u3000+', ' ', text)  # 全角空格
    text = re.sub(r'\u00A0+', ' ', text)  # 不换行空格

    # 清理换行符后的多余空格
    text = re.sub(r'\n +', '\n', text)

    # 清理空格后的换行符
    text = re.sub(r' +\n', '\n', text)

    return text.strip()


def classify_content_type(content: str, lesson_title: str, unit_title: str) -> str:
    """
    分类内容类型
    返回: 'lesson_main', 'exercise', 'instruction', 'supplementary', 'mixed'
    """
    if pd.isna(content) or not content:
        return 'empty'

    content_lower = str(content).lower()

    # 课文主要内容标识符
    lesson_main_indicators = [
        '本文作者', '选作课文时有改动', '早晨，', '从前，', '有一个',
        '三国', '宋', '唐', '清', '古诗', '本文', '故事'
    ]

    # 练习和活动标识符
    exercise_indicators = [
        '朗读课文', '背诵课文', '想一想', '说一说', '写一写', '练习',
        '小练笔', '习作', '口语交际', '和同学交流', '猜猜他是谁',
        '写日记', '做游戏', '小组活动', '讨论', '互相', '展示'
    ]

    # 教学指导类标识符
    instruction_indicators = [
        '学习目标', '重点', '难点', '方法', '提示', '注意', '要求',
        '教学建议', '资料袋', '注释', '词语表', '识字表', '写字表'
    ]

    # 辅助材料标识符
    supplementary_indicators = [
        '资料袋', '日积月累', '阅读链接', '书写提示', '语文园地',
        '交流平台', '词句段运用', '识字表', '写字表', '词语表',
        '目录', '序', '版权页', '封底', '封面'
    ]

    # 计算各类别得分
    lesson_score = sum(1 for indicator in lesson_main_indicators if indicator in content_lower)
    exercise_score = sum(1 for indicator in exercise_indicators if indicator in content_lower)
    instruction_score = sum(1 for indicator in instruction_indicators if indicator in content_lower)
    supplementary_score = sum(1 for indicator in supplementary_indicators if indicator in content_lower)

    # 判断内容类型
    if supplementary_score >= 2:
        return 'supplementary'
    elif exercise_score >= 2:
        return 'exercise'
    elif instruction_score >= 2:
        return 'instruction'
    elif lesson_score >= 1:
        return 'lesson_main'
    else:
        # 基于内容长度和结构进行二次判断
        if len(content) > 200 and '。' in content and '，' in content:
            return 'lesson_main'  # 长文本且包含标点符号，可能是课文
        elif len(content) < 100 and ('？' in content or '！' in content):
            return 'exercise'  # 短文本且包含问号感叹号，可能是练习
        else:
            return 'mixed'


def extract_lesson_main_content(content: str) -> str:
    """提取课文主体内容，移除练习题和指导说明"""
    if pd.isna(content) or not content:
        return content

    lines = str(content).split('\n')
    lesson_lines = []
    skip_patterns = [
        r'朗读课文', r'背诵课文', r'默写', r'想一想', r'说一说', r'写一写',
        r'和同学交流', r'小练笔', r'习作', r'口语交际', r'资料袋',
        r'注释', r'日积月累', r'阅读链接', r'书写提示', r'语文园地',
        r'交流平台', r'词句段运用', r'识字表', r'写字表', r'词语表',
        r'练习', r'选择', r'下面的', r'怎样', r'如何', r'说说',
        r'小组活动', r'讨论', r'展示', r'猜猜', r'游戏'
    ]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 跳过明显的练习和指导内容
        is_skip_line = any(re.search(pattern, line) for pattern in skip_patterns)

        # 保留课文主体内容
        if not is_skip_line:
            # 跳过纯练习题目（如选择、填空等）
            if len(line) > 10 and not line.startswith(('1.', '2.', '3.', '（', '※', '▢')):
                lesson_lines.append(line)

    return '\n'.join(lesson_lines)


def fix_lesson_title(row: pd.Series) -> str:
    """修复课程标题"""
    current_title = str(row.get('lesson_title', '')).strip()

    # 如果标题为空或明显不正确，尝试从内容中提取
    if not current_title or current_title in ['序', '目录', '语文园地', '']:
        content = str(row.get('content', ''))

        # 尝试从内容中提取真实的课程标题
        title_patterns = [
            r'([^。\n]{2,8}?)\s*本文作者',
            r'([^。\n]{2,8}?)\s*选作课文时有改动',
            r'([^。\n]{2,10}?)\s*唐\s+\w+',
            r'([^。\n]{2,10}?)\s*宋\s+\w+',
            r'([^。\n]{2,10}?)\s*清\s+\w+',
        ]

        for pattern in title_patterns:
            match = re.search(pattern, content)
            if match:
                extracted_title = match.group(1).strip()
                if len(extracted_title) >= 2 and len(extracted_title) <= 12:
                    return extracted_title

    # 清理现有标题
    if current_title:
        # 移除不必要的标点符号
        current_title = re.sub(r'[：:，,\s]+$', '', current_title)
        current_title = current_title.strip()

        # 如果标题太短，可能是错误的
        if len(current_title) < 2:
            return ''

    return current_title


def enhance_csv_data(df: pd.DataFrame) -> pd.DataFrame:
    """增强CSV数据，添加内容分类和清理后的内容"""
    enhanced_df = df.copy()

    # 添加新列
    enhanced_df['content_type'] = ''
    enhanced_df['cleaned_content'] = ''
    enhanced_df['lesson_main_content'] = ''
    enhanced_df['fixed_lesson_title'] = ''

    print_status("开始处理CSV数据行", "🔧")

    for idx, row in enhanced_df.iterrows():
        if idx % 20 == 0:
            print_status(f"处理进度: {idx+1}/{len(enhanced_df)}", "📊")

        # 获取原始数据
        content = str(row.get('content', ''))
        lesson_title = str(row.get('lesson_title', ''))
        unit_title = str(row.get('unit_title', ''))

        # 1. 清理空白
        cleaned_content = clean_whitespace(content)
        enhanced_df.at[idx, 'cleaned_content'] = cleaned_content

        # 2. 分类内容
        content_type = classify_content_type(cleaned_content, lesson_title, unit_title)
        enhanced_df.at[idx, 'content_type'] = content_type

        # 3. 提取课文主体内容
        if content_type in ['lesson_main', 'mixed']:
            lesson_main = extract_lesson_main_content(cleaned_content)
            enhanced_df.at[idx, 'lesson_main_content'] = lesson_main

        # 4. 修复课程标题
        fixed_title = fix_lesson_title(row)
        enhanced_df.at[idx, 'fixed_lesson_title'] = fixed_title

    return enhanced_df


def generate_summary_report(enhanced_df: pd.DataFrame) -> Dict:
    """生成处理结果摘要报告"""
    report = {
        'total_records': len(enhanced_df),
        'content_types': enhanced_df['content_type'].value_counts().to_dict(),
        'title_fixes': 0,
        'content_cleaned': 0,
        'lesson_main_extracted': 0
    }

    # 统计修复的标题数量
    original_titles = enhanced_df['lesson_title'].fillna('')
    fixed_titles = enhanced_df['fixed_lesson_title'].fillna('')
    report['title_fixes'] = sum(1 for orig, fixed in zip(original_titles, fixed_titles)
                               if orig != fixed and fixed != '')

    # 统计清理的内容数量
    original_content = enhanced_df['content'].fillna('')
    cleaned_content = enhanced_df['cleaned_content'].fillna('')
    report['content_cleaned'] = sum(1 for orig, clean in zip(original_content, cleaned_content)
                                   if orig != clean)

    # 统计提取的课文主体内容数量
    lesson_main_content = enhanced_df['lesson_main_content'].fillna('')
    report['lesson_main_extracted'] = sum(1 for content in lesson_main_content if content != '')

    return report


def main():
    """主函数"""
    print_status("开始CSV内容清理和精炼处理", "🚀")
    print("=" * 60)

    # 设置文件路径
    input_csv = project_root / "exports" / "语文三上_content_fixed.csv"
    output_csv = project_root / "exports" / "语文三上_content_refined.csv"

    if not input_csv.exists():
        print_status(f"输入文件不存在: {input_csv}", "❌")
        return 1

    try:
        # 读取原始CSV文件
        print_status(f"读取CSV文件: {input_csv}", "📖")
        df = pd.read_csv(input_csv)
        print_status(f"原始CSV包含 {len(df)} 条记录", "📊")

        # 处理数据
        enhanced_df = enhance_csv_data(df)

        # 生成报告
        report = generate_summary_report(enhanced_df)

        # 保存精炼后的CSV文件
        print_status(f"保存精炼后的CSV文件: {output_csv}", "💾")
        enhanced_df.to_csv(output_csv, index=False, encoding='utf-8')

        # 显示处理结果
        print("\n" + "=" * 60)
        print_status("✅ CSV内容清理完成！", "✅")
        print(f"📊 处理记录数: {report['total_records']}")
        print(f"🧹 内容清理数: {report['content_cleaned']}")
        print(f"🏷️ 标题修复数: {report['title_fixes']}")
        print(f"📚 课文主体提取数: {report['lesson_main_extracted']}")

        print("\n📋 内容类型分布:")
        for content_type, count in report['content_types'].items():
            type_name = {
                'lesson_main': '课文主体',
                'exercise': '练习活动',
                'instruction': '教学指导',
                'supplementary': '辅助材料',
                'mixed': '混合内容',
                'empty': '空白内容'
            }.get(content_type, content_type)
            print(f"   {type_name}: {count}")

        print(f"\n📄 输出文件: {output_csv}")
        print("\n💡 后续建议:")
        print("   1. 检查精炼后的CSV文件内容")
        print("   2. 验证课文主体内容的提取质量")
        print("   3. 确认修复的课程标题是否正确")
        print("   4. 使用精炼后的CSV文件重新导入向量数据库")

        return 0

    except Exception as e:
        print_status(f"CSV处理失败: {e}", "❌")
        return 1


if __name__ == "__main__":
    sys.exit(main())